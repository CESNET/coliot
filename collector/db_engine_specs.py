# -*- coding: utf-8 -*-
# pylint: disable=C,R,W
"""Compatibility layer for different database engines

This modules stores logic specific to different database engines. Things
like time-related functions that are similar but not identical, or
information as to expose certain features or not and how to expose them.

For instance, Hive/Presto supports partitions and have a specific API to
list partitions. Other databases like Vertica also support partitions but
have different API to get to them. Other databases don't support partitions
at all. The classes here will use a common interface to specify all this.

The general idea is to use static classes and an inheritance scheme.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict, namedtuple
import inspect
import logging
import os
import re
import textwrap
import time

import boto3
from flask import g
from flask_babel import lazy_gettext as _
import pandas
from past.builtins import basestring
import sqlalchemy as sqla
from sqlalchemy import select
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.sql import text
from sqlalchemy.sql.expression import TextAsFrom
import sqlparse
from tableschema import Table
from werkzeug.utils import secure_filename

from superset import app, cache_util, conf, db, sql_parse, utils
from superset.exceptions import SupersetTemplateException
from superset.utils import QueryStatus

config = app.config

tracking_url_trans = conf.get('TRACKING_URL_TRANSFORMER')
hive_poll_interval = conf.get('HIVE_POLL_INTERVAL')

Grain = namedtuple('Grain', 'name label function duration')

builtin_time_grains = {
    None: 'Time Column',
    'PT1S': 'second',
    'PT1M': 'minute',
    'PT5M': '5 minute',
    'PT10M': '10 minute',
    'PT15M': '15 minute',
    'PT0.5H': 'half hour',
    'PT1H': 'hour',
    'P1D': 'day',
    'P1W': 'week',
    'P1M': 'month',
    'P0.25Y': 'quarter',
    'P1Y': 'year',
    '1969-12-28T00:00:00Z/P1W': 'week_start_sunday',
    '1969-12-29T00:00:00Z/P1W': 'week_start_monday',
    'P1W/1970-01-03T00:00:00Z': 'week_ending_saturday',
    'P1W/1970-01-04T00:00:00Z': 'week_ending_sunday',
}


def _create_time_grains_tuple(time_grains, time_grain_functions, blacklist):
    ret_list = []
    blacklist = blacklist if blacklist else []
    for duration, func in time_grain_functions.items():
        if duration not in blacklist:
            name = time_grains.get(duration)
            ret_list.append(Grain(name, _(name), func, duration))
    return tuple(ret_list)


class LimitMethod(object):
    """Enum the ways that limits can be applied"""
    FETCH_MANY = 'fetch_many'
    WRAP_SQL = 'wrap_sql'
    FORCE_LIMIT = 'force_limit'


class BaseEngineSpec(object):

    """Abstract class for database engine specific configurations"""

    engine = 'base'  # str as defined in sqlalchemy.engine.engine
    time_grain_functions = {}
    time_groupby_inline = False
    limit_method = LimitMethod.FORCE_LIMIT
    time_secondary_columns = False
    inner_joins = True
    allows_subquery = True
    consistent_case_sensitivity = True  # do results have same case as qry for col names?
    arraysize = None

    @classmethod
    def get_time_grains(cls):
        blacklist = config.get('TIME_GRAIN_BLACKLIST', [])
        grains = builtin_time_grains.copy()
        grains.update(config.get('TIME_GRAIN_ADDONS', {}))
        grain_functions = cls.time_grain_functions.copy()
        grain_addon_functions = config.get('TIME_GRAIN_ADDON_FUNCTIONS', {})
        grain_functions.update(grain_addon_functions.get(cls.engine, {}))
        return _create_time_grains_tuple(grains, grain_functions, blacklist)

    @classmethod
    def fetch_data(cls, cursor, limit):
        if cls.arraysize:
            cursor.arraysize = cls.arraysize
        if cls.limit_method == LimitMethod.FETCH_MANY:
            return cursor.fetchmany(limit)
        return cursor.fetchall()

    @classmethod
    def epoch_to_dttm(cls):
        raise NotImplementedError()

    @classmethod
    def epoch_ms_to_dttm(cls):
        return cls.epoch_to_dttm().replace('{col}', '({col}/1000.000)')

    @classmethod
    def get_datatype(cls, type_code):
        if isinstance(type_code, basestring) and len(type_code):
            return type_code.upper()

    @classmethod
    def extra_table_metadata(cls, database, table_name, schema_name):
        """Returns engine-specific table metadata"""
        return {}

    @classmethod
    def apply_limit_to_sql(cls, sql, limit, database):
        """Alters the SQL statement to apply a LIMIT clause"""
        if cls.limit_method == LimitMethod.WRAP_SQL:
            sql = sql.strip('\t\n ;')
            qry = (
                select('*')
                .select_from(
                    TextAsFrom(text(sql), ['*']).alias('inner_qry'),
                )
                .limit(limit)
            )
            return database.compile_sqla_query(qry)
        elif LimitMethod.FORCE_LIMIT:
            parsed_query = sql_parse.SupersetQuery(sql)
            sql = parsed_query.get_query_with_new_limit(limit)
        return sql

    @classmethod
    def get_limit_from_sql(cls, sql):
        parsed_query = sql_parse.SupersetQuery(sql)
        return parsed_query.limit

    @classmethod
    def get_query_with_new_limit(cls, sql, limit):
        parsed_query = sql_parse.SupersetQuery(sql)
        return parsed_query.get_query_with_new_limit(limit)

    @staticmethod
    def csv_to_df(**kwargs):
        kwargs['filepath_or_buffer'] = \
            config['UNIREC_FOLDER'] + kwargs['filepath_or_buffer']
        kwargs['encoding'] = 'utf-8'
        kwargs['iterator'] = True
        chunks = pandas.read_csv(**kwargs)
        df = pandas.DataFrame()
        df = pandas.concat(chunk for chunk in chunks)
        return df

    @staticmethod
    def df_to_db(df, table, **kwargs):
        df.to_sql(**kwargs)
        table.user_id = g.user.id
        table.schema = kwargs['schema']
        table.fetch_metadata()
        db.session.add(table)
        db.session.commit()

    @staticmethod
    def create_table_from_csv(form, table):
        def _allowed_file(filename):
            # Only allow specific file extensions as specified in the config
            extension = os.path.splitext(filename)[0] #TODO [1]
            #return extension and extension[1:] in config['ALLOWED_EXTENSIONS']
        return extension

        filename = secure_filename(form.unirec_file.data)
        if not _allowed_file(filename):
            raise Exception('Invalid file type selected')
        kwargs = {
            'filepath_or_buffer': filename,
            'sep': ',',
            'header': form.header.data if form.header.data else 0,
            'index_col': form.index_col.data,
            'mangle_dupe_cols': form.mangle_dupe_cols.data,
            'skipinitialspace': form.skipinitialspace.data,
            'skiprows': form.skiprows.data,
            'nrows': form.nrows.data,
            'skip_blank_lines': form.skip_blank_lines.data,
            'parse_dates': form.parse_dates.data,
            'infer_datetime_format': form.infer_datetime_format.data,
            'chunksize': 10000,
        }
        df = BaseEngineSpec.csv_to_df(**kwargs)

        df_to_db_kwargs = {
            'table': table,
            'df': df,
            'name': form.name.data,
            'con': create_engine(form.con.data.sqlalchemy_uri_decrypted, echo=False),
            'schema': form.schema.data,
            'if_exists': form.if_exists.data,
            'index': form.index.data,
            'index_label': form.index_label.data,
            'chunksize': 10000,
        }

        BaseEngineSpec.df_to_db(**df_to_db_kwargs)

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    @cache_util.memoized_func(
        timeout=600,
        key=lambda *args, **kwargs: 'db:{}:{}'.format(args[0].id, args[1]))
    def fetch_result_sets(cls, db, datasource_type, force=False):
        """Returns the dictionary {schema : [result_set_name]}.

        Datasource_type can be 'table' or 'view'.
        Empty schema corresponds to the list of full names of the all
        tables or views: <schema>.<result_set_name>.
        """
        schemas = db.inspector.get_schema_names()
        result_sets = {}
        all_result_sets = []
        for schema in schemas:
            if datasource_type == 'table':
                result_sets[schema] = sorted(
                    db.inspector.get_table_names(schema))
            elif datasource_type == 'view':
                result_sets[schema] = sorted(
                    db.inspector.get_view_names(schema))
            all_result_sets += [
                '{}.{}'.format(schema, t) for t in result_sets[schema]]
        if all_result_sets:
            result_sets[''] = all_result_sets
        return result_sets

    @classmethod
    def handle_cursor(cls, cursor, query, session):
        """Handle a live cursor between the execute and fetchall calls

        The flow works without this method doing anything, but it allows
        for handling the cursor and updating progress information in the
        query object"""
        pass

    @classmethod
    def extract_error_message(cls, e):
        """Extract error message for queries"""
        return utils.error_msg_from_exception(e)

    @classmethod
    def adjust_database_uri(cls, uri, selected_schema):
        """Based on a URI and selected schema, return a new URI

        The URI here represents the URI as entered when saving the database,
        ``selected_schema`` is the schema currently active presumably in
        the SQL Lab dropdown. Based on that, for some database engine,
        we can return a new altered URI that connects straight to the
        active schema, meaning the users won't have to prefix the object
        names by the schema name.

        Some databases engines have 2 level of namespacing: database and
        schema (postgres, oracle, mssql, ...)
        For those it's probably better to not alter the database
        component of the URI with the schema name, it won't work.

        Some database drivers like presto accept '{catalog}/{schema}' in
        the database component of the URL, that can be handled here.
        """
        return uri

    @classmethod
    def patch(cls):
        pass

    @classmethod
    def get_schema_names(cls, inspector):
        return inspector.get_schema_names()

    @classmethod
    def get_table_names(cls, schema, inspector):
        return sorted(inspector.get_table_names(schema))

    @classmethod
    def where_latest_partition(
            cls, table_name, schema, database, qry, columns=None):
        return False

    @classmethod
    def _get_fields(cls, cols):
        return [sqla.column(c.get('name')) for c in cols]

    @classmethod
    def select_star(cls, my_db, table_name, engine, schema=None, limit=100,
                    show_cols=False, indent=True, latest_partition=True,
                    cols=None):
        fields = '*'
        cols = cols or []
        if (show_cols or latest_partition) and not cols:
            cols = my_db.get_columns(table_name, schema)

        if show_cols:
            fields = cls._get_fields(cols)
        quote = engine.dialect.identifier_preparer.quote
        if schema:
            full_table_name = quote(schema) + '.' + quote(table_name)
        else:
            full_table_name = quote(table_name)

        qry = select(fields).select_from(text(full_table_name))

        if limit:
            qry = qry.limit(limit)
        if latest_partition:
            partition_query = cls.where_latest_partition(
                table_name, schema, my_db, qry, columns=cols)
            if partition_query != False:  # noqa
                qry = partition_query
        sql = my_db.compile_sqla_query(qry)
        if indent:
            sql = sqlparse.format(sql, reindent=True)
        return sql

    @classmethod
    def modify_url_for_impersonation(cls, url, impersonate_user, username):
        """
        Modify the SQL Alchemy URL object with the user to impersonate if applicable.
        :param url: SQLAlchemy URL object
        :param impersonate_user: Bool indicating if impersonation is enabled
        :param username: Effective username
        """
        if impersonate_user is not None and username is not None:
            url.username = username

    @classmethod
    def get_configuration_for_impersonation(cls, uri, impersonate_user, username):
        """
        Return a configuration dictionary that can be merged with other configs
        that can set the correct properties for impersonating users
        :param uri: URI string
        :param impersonate_user: Bool indicating if impersonation is enabled
        :param username: Effective username
        :return: Dictionary with configs required for impersonation
        """
        return {}

    @classmethod
    def execute(cls, cursor, query, async=False):
        if cls.arraysize:
            cursor.arraysize = cls.arraysize
        cursor.execute(query)

    @classmethod
    def adjust_df_column_names(cls, df, fd):
        """Based of fields in form_data, return dataframe with new column names

        Usually sqla engines return column names whose case matches that of the
        original query. For example:
            SELECT 1 as col1, 2 as COL2, 3 as Col_3
        will usually result in the following df.columns:
            ['col1', 'COL2', 'Col_3'].
        For these engines there is no need to adjust the dataframe column names
        (default behavior). However, some engines (at least Snowflake, Oracle and
        Redshift) return column names with different case than in the original query,
        usually all uppercase. For these the column names need to be adjusted to
        correspond to the case of the fields specified in the form data for Viz
        to work properly. This adjustment can be done here.
        """
        if cls.consistent_case_sensitivity:
            return df
        else:
            return cls.align_df_col_names_with_form_data(df, fd)

    @staticmethod
    def align_df_col_names_with_form_data(df, fd):
        """Helper function to rename columns that have changed case during query.

        Returns a dataframe where column names have been adjusted to correspond with
        column names in form data (case insensitive). Examples:
        dataframe: 'col1', form_data: 'col1' -> no change
        dataframe: 'COL1', form_data: 'col1' -> dataframe column renamed: 'col1'
        dataframe: 'col1', form_data: 'Col1' -> dataframe column renamed: 'Col1'
        """

        columns = set()
        lowercase_mapping = {}

        metrics = utils.get_metric_names(fd.get('metrics', []))
        groupby = fd.get('groupby', [])
        other_cols = [utils.DTTM_ALIAS]
        for col in metrics + groupby + other_cols:
            columns.add(col)
            lowercase_mapping[col.lower()] = col

        rename_cols = {}
        for col in df.columns:
            if col not in columns:
                orig_col = lowercase_mapping.get(col.lower())
                if orig_col:
                    rename_cols[col] = orig_col

        return df.rename(index=str, columns=rename_cols)


class PostgresBaseEngineSpec(BaseEngineSpec):
    """ Abstract class for Postgres 'like' databases """

    engine = ''

    time_grain_functions = {
        None: '{col}',
        'PT1S': "DATE_TRUNC('second', {col}) AT TIME ZONE 'UTC'",
        'PT1M': "DATE_TRUNC('minute', {col}) AT TIME ZONE 'UTC'",
        'PT1H': "DATE_TRUNC('hour', {col}) AT TIME ZONE 'UTC'",
        'P1D': "DATE_TRUNC('day', {col}) AT TIME ZONE 'UTC'",
        'P1W': "DATE_TRUNC('week', {col}) AT TIME ZONE 'UTC'",
        'P1M': "DATE_TRUNC('month', {col}) AT TIME ZONE 'UTC'",
        'P0.25Y': "DATE_TRUNC('quarter', {col}) AT TIME ZONE 'UTC'",
        'P1Y': "DATE_TRUNC('year', {col}) AT TIME ZONE 'UTC'",
    }

    @classmethod
    def fetch_data(cls, cursor, limit):
        if not cursor.description:
            return []
        if cls.limit_method == LimitMethod.FETCH_MANY:
            return cursor.fetchmany(limit)
        return cursor.fetchall()

    @classmethod
    def epoch_to_dttm(cls):
        return "(timestamp 'epoch' + {col} * interval '1 second')"

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))


class PostgresEngineSpec(PostgresBaseEngineSpec):
    engine = 'postgresql'

    @classmethod
    def get_table_names(cls, schema, inspector):
        """Need to consider foreign tables for PostgreSQL"""
        tables = inspector.get_table_names(schema)
        tables.extend(inspector.get_foreign_table_names(schema))
        return sorted(tables)


class SnowflakeEngineSpec(PostgresBaseEngineSpec):
    engine = 'snowflake'
    consistent_case_sensitivity = False
    time_grain_functions = {
        None: '{col}',
        'PT1S': "DATE_TRUNC('SECOND', {col})",
        'PT1M': "DATE_TRUNC('MINUTE', {col})",
        'PT5M': "DATEADD(MINUTE, FLOOR(DATE_PART(MINUTE, {col}) / 5) * 5, \
                DATE_TRUNC('HOUR', {col}))",
        'PT10M': "DATEADD(MINUTE, FLOOR(DATE_PART(MINUTE, {col}) / 10) * 10, \
                 DATE_TRUNC('HOUR', {col}))",
        'PT15M': "DATEADD(MINUTE, FLOOR(DATE_PART(MINUTE, {col}) / 15) * 15, \
                 DATE_TRUNC('HOUR', {col}))",
        'PT0.5H': "DATEADD(MINUTE, FLOOR(DATE_PART(MINUTE, {col}) / 30) * 30, \
                  DATE_TRUNC('HOUR', {col}))",
        'PT1H': "DATE_TRUNC('HOUR', {col})",
        'P1D': "DATE_TRUNC('DAY', {col})",
        'P1W': "DATE_TRUNC('WEEK', {col})",
        'P1M': "DATE_TRUNC('MONTH', {col})",
        'P0.25Y': "DATE_TRUNC('QUARTER', {col})",
        'P1Y': "DATE_TRUNC('YEAR', {col})",
    }

    @classmethod
    def adjust_database_uri(cls, uri, selected_schema=None):
        database = uri.database
        if '/' in uri.database:
            database = uri.database.split('/')[0]
        if selected_schema:
            uri.database = database + '/' + selected_schema
        return uri


class VerticaEngineSpec(PostgresBaseEngineSpec):
    engine = 'vertica'


class RedshiftEngineSpec(PostgresBaseEngineSpec):
    engine = 'redshift'
    consistent_case_sensitivity = False


class OracleEngineSpec(PostgresBaseEngineSpec):
    engine = 'oracle'
    limit_method = LimitMethod.WRAP_SQL
    consistent_case_sensitivity = False

    time_grain_functions = {
        None: '{col}',
        'PT1S': 'CAST({col} as DATE)',
        'PT1M': "TRUNC(TO_DATE({col}), 'MI')",
        'PT1H': "TRUNC(TO_DATE({col}), 'HH')",
        'P1D': "TRUNC(TO_DATE({col}), 'DDD')",
        'P1W': "TRUNC(TO_DATE({col}), 'WW')",
        'P1M': "TRUNC(TO_DATE({col}), 'MONTH')",
        'P0.25Y': "TRUNC(TO_DATE({col}), 'Q')",
        'P1Y': "TRUNC(TO_DATE({col}), 'YEAR')",
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        return (
            """TO_TIMESTAMP('{}', 'YYYY-MM-DD"T"HH24:MI:SS.ff6')"""
        ).format(dttm.isoformat())


class Db2EngineSpec(BaseEngineSpec):
    engine = 'ibm_db_sa'
    limit_method = LimitMethod.WRAP_SQL
    time_grain_functions = {
        None: '{col}',
        'PT1S': 'CAST({col} as TIMESTAMP)'
                ' - MICROSECOND({col}) MICROSECONDS',
        'PT1M': 'CAST({col} as TIMESTAMP)'
                ' - SECOND({col}) SECONDS'
                ' - MICROSECOND({col}) MICROSECONDS',
        'PT1H': 'CAST({col} as TIMESTAMP)'
                ' - MINUTE({col}) MINUTES'
                ' - SECOND({col}) SECONDS'
                ' - MICROSECOND({col}) MICROSECONDS ',
        'P1D': 'CAST({col} as TIMESTAMP)'
               ' - HOUR({col}) HOURS'
               ' - MINUTE({col}) MINUTES'
               ' - SECOND({col}) SECONDS'
               ' - MICROSECOND({col}) MICROSECONDS',
        'P1W': '{col} - (DAYOFWEEK({col})) DAYS',
        'P1M': '{col} - (DAY({col})-1) DAYS',
        'P0.25Y': '{col} - (DAY({col})-1) DAYS'
                  ' - (MONTH({col})-1) MONTHS'
                  ' + ((QUARTER({col})-1) * 3) MONTHS',
        'P1Y': '{col} - (DAY({col})-1) DAYS'
               ' - (MONTH({col})-1) MONTHS',
    }

    @classmethod
    def epoch_to_dttm(cls):
        return "(TIMESTAMP('1970-01-01', '00:00:00') + {col} SECONDS)"

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        return "'{}'".format(dttm.strftime('%Y-%m-%d-%H.%M.%S'))


class SqliteEngineSpec(BaseEngineSpec):
    engine = 'sqlite'

    time_grain_functions = {
        None: '{col}',
        'PT1H': "DATETIME(STRFTIME('%Y-%m-%dT%H:00:00', {col}))",
        'P1D': 'DATE({col})',
        'P1W': "DATE({col}, -strftime('%W', {col}) || ' days')",
        'P1M': "DATE({col}, -strftime('%d', {col}) || ' days', '+1 day')",
        'P1Y': "DATETIME(STRFTIME('%Y-01-01T00:00:00', {col}))",
        'P1W/1970-01-03T00:00:00Z': "DATE({col}, 'weekday 6')",
        '1969-12-28T00:00:00Z/P1W': "DATE({col}, 'weekday 0', '-7 days')",
    }

    @classmethod
    def epoch_to_dttm(cls):
        return "datetime({col}, 'unixepoch')"

    @classmethod
    @cache_util.memoized_func(
        timeout=600,
        key=lambda *args, **kwargs: 'db:{}:{}'.format(args[0].id, args[1]))
    def fetch_result_sets(cls, db, datasource_type, force=False):
        schemas = db.inspector.get_schema_names()
        result_sets = {}
        all_result_sets = []
        schema = schemas[0]
        if datasource_type == 'table':
            result_sets[schema] = sorted(db.inspector.get_table_names())
        elif datasource_type == 'view':
            result_sets[schema] = sorted(db.inspector.get_view_names())
        all_result_sets += [
            '{}.{}'.format(schema, t) for t in result_sets[schema]]
        if all_result_sets:
            result_sets[''] = all_result_sets
        return result_sets

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        iso = dttm.isoformat().replace('T', ' ')
        if '.' not in iso:
            iso += '.000000'
        return "'{}'".format(iso)

    @classmethod
    def get_table_names(cls, schema, inspector):
        """Need to disregard the schema for Sqlite"""
        return sorted(inspector.get_table_names())


class MySQLEngineSpec(BaseEngineSpec):
    engine = 'mysql'

    time_grain_functions = {
        None: '{col}',
        'PT1S': 'DATE_ADD(DATE({col}), '
              'INTERVAL (HOUR({col})*60*60 + MINUTE({col})*60'
              ' + SECOND({col})) SECOND)',
        'PT1M': 'DATE_ADD(DATE({col}), '
              'INTERVAL (HOUR({col})*60 + MINUTE({col})) MINUTE)',
        'PT1H': 'DATE_ADD(DATE({col}), '
              'INTERVAL HOUR({col}) HOUR)',
        'P1D': 'DATE({col})',
        'P1W': 'DATE(DATE_SUB({col}, '
              'INTERVAL DAYOFWEEK({col}) - 1 DAY))',
        'P1M': 'DATE(DATE_SUB({col}, '
              'INTERVAL DAYOFMONTH({col}) - 1 DAY))',
        'P0.25Y': 'MAKEDATE(YEAR({col}), 1) '
              '+ INTERVAL QUARTER({col}) QUARTER - INTERVAL 1 QUARTER',
        'P1Y': 'DATE(DATE_SUB({col}, '
              'INTERVAL DAYOFYEAR({col}) - 1 DAY))',
        '1969-12-29T00:00:00Z/P1W': 'DATE(DATE_SUB({col}, '
              'INTERVAL DAYOFWEEK(DATE_SUB({col}, INTERVAL 1 DAY)) - 1 DAY))',
    }

    type_code_map = {}  # loaded from get_datatype only if needed

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        if target_type.upper() in ('DATETIME', 'DATE'):
            return "STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s')".format(
                dttm.strftime('%Y-%m-%d %H:%M:%S'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def adjust_database_uri(cls, uri, selected_schema=None):
        if selected_schema:
            uri.database = selected_schema
        return uri

    @classmethod
    def get_datatype(cls, type_code):
        if not cls.type_code_map:
            # only import and store if needed at least once
            import MySQLdb
            ft = MySQLdb.constants.FIELD_TYPE
            cls.type_code_map = {
                getattr(ft, k): k
                for k in dir(ft)
                if not k.startswith('_')
            }
        datatype = type_code
        if isinstance(type_code, int):
            datatype = cls.type_code_map.get(type_code)
        if datatype and isinstance(datatype, basestring) and len(datatype):
            return datatype

    @classmethod
    def epoch_to_dttm(cls):
        return 'from_unixtime({col})'

    @classmethod
    def extract_error_message(cls, e):
        """Extract error message for queries"""
        message = str(e)
        try:
            if isinstance(e.args, tuple) and len(e.args) > 1:
                message = e.args[1]
        except Exception:
            pass
        return message


class PrestoEngineSpec(BaseEngineSpec):
    engine = 'presto'

    time_grain_functions = {
        None: '{col}',
        'PT1S': "date_trunc('second', CAST({col} AS TIMESTAMP))",
        'PT1M': "date_trunc('minute', CAST({col} AS TIMESTAMP))",
        'PT1H': "date_trunc('hour', CAST({col} AS TIMESTAMP))",
        'P1D': "date_trunc('day', CAST({col} AS TIMESTAMP))",
        'P1W': "date_trunc('week', CAST({col} AS TIMESTAMP))",
        'P1M': "date_trunc('month', CAST({col} AS TIMESTAMP))",
        'P0.25Y': "date_trunc('quarter', CAST({col} AS TIMESTAMP))",
        'P1Y': "date_trunc('year', CAST({col} AS TIMESTAMP))",
        'P1W/1970-01-03T00:00:00Z':
            "date_add('day', 5, date_trunc('week', date_add('day', 1, \
            CAST({col} AS TIMESTAMP))))",
        '1969-12-28T00:00:00Z/P1W':
            "date_add('day', -1, date_trunc('week', \
            date_add('day', 1, CAST({col} AS TIMESTAMP))))",
    }

    @classmethod
    def adjust_database_uri(cls, uri, selected_schema=None):
        database = uri.database
        if selected_schema and database:
            if '/' in database:
                database = database.split('/')[0] + '/' + selected_schema
            else:
                database += '/' + selected_schema
            uri.database = database
        return uri

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "from_iso8601_date('{}')".format(dttm.isoformat()[:10])
        if tt == 'TIMESTAMP':
            return "from_iso8601_timestamp('{}')".format(dttm.isoformat())
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def epoch_to_dttm(cls):
        return 'from_unixtime({col})'

    @classmethod
    @cache_util.memoized_func(
        timeout=600,
        key=lambda *args, **kwargs: 'db:{}:{}'.format(args[0].id, args[1]))
    def fetch_result_sets(cls, db, datasource_type, force=False):
        """Returns the dictionary {schema : [result_set_name]}.

        Datasource_type can be 'table' or 'view'.
        Empty schema corresponds to the list of full names of the all
        tables or views: <schema>.<result_set_name>.
        """
        result_set_df = db.get_df(
            """SELECT table_schema, table_name FROM INFORMATION_SCHEMA.{}S
               ORDER BY concat(table_schema, '.', table_name)""".format(
                datasource_type.upper(),
            ),
            None)
        result_sets = defaultdict(list)
        for unused, row in result_set_df.iterrows():
            result_sets[row['table_schema']].append(row['table_name'])
            result_sets[''].append('{}.{}'.format(
                row['table_schema'], row['table_name']))
        return result_sets

    @classmethod
    def extra_table_metadata(cls, database, table_name, schema_name):
        indexes = database.get_indexes(table_name, schema_name)
        if not indexes:
            return {}
        cols = indexes[0].get('column_names', [])
        full_table_name = table_name
        if schema_name and '.' not in table_name:
            full_table_name = '{}.{}'.format(schema_name, table_name)
        pql = cls._partition_query(full_table_name)
        col_name, latest_part = cls.latest_partition(
            table_name, schema_name, database, show_first=True)
        return {
            'partitions': {
                'cols': cols,
                'latest': {col_name: latest_part},
                'partitionQuery': pql,
            },
        }

    @classmethod
    def handle_cursor(cls, cursor, query, session):
        """Updates progress information"""
        logging.info('Polling the cursor for progress')
        polled = cursor.poll()
        # poll returns dict -- JSON status information or ``None``
        # if the query is done
        # https://github.com/dropbox/PyHive/blob/
        # b34bdbf51378b3979eaf5eca9e956f06ddc36ca0/pyhive/presto.py#L178
        while polled:
            # Update the object and wait for the kill signal.
            stats = polled.get('stats', {})

            query = session.query(type(query)).filter_by(id=query.id).one()
            if query.status in [QueryStatus.STOPPED, QueryStatus.TIMED_OUT]:
                cursor.cancel()
                break

            if stats:
                state = stats.get('state')

                # if already finished, then stop polling
                if state == 'FINISHED':
                    break

                completed_splits = float(stats.get('completedSplits'))
                total_splits = float(stats.get('totalSplits'))
                if total_splits and completed_splits:
                    progress = 100 * (completed_splits / total_splits)
                    logging.info(
                        'Query progress: {} / {} '
                        'splits'.format(completed_splits, total_splits))
                    if progress > query.progress:
                        query.progress = progress
                    session.commit()
            time.sleep(1)
            logging.info('Polling the cursor for progress')
            polled = cursor.poll()

    @classmethod
    def extract_error_message(cls, e):
        if (
                hasattr(e, 'orig') and
                type(e.orig).__name__ == 'DatabaseError' and
                isinstance(e.orig[0], dict)):
            error_dict = e.orig[0]
            return '{} at {}: {}'.format(
                error_dict.get('errorName'),
                error_dict.get('errorLocation'),
                error_dict.get('message'),
            )
        if (
                type(e).__name__ == 'DatabaseError' and
                hasattr(e, 'args') and
                len(e.args) > 0
        ):
            error_dict = e.args[0]
            return error_dict.get('message')
        return utils.error_msg_from_exception(e)

    @classmethod
    def _partition_query(
            cls, table_name, limit=0, order_by=None, filters=None):
        """Returns a partition query

        :param table_name: the name of the table to get partitions from
        :type table_name: str
        :param limit: the number of partitions to be returned
        :type limit: int
        :param order_by: a list of tuples of field name and a boolean
            that determines if that field should be sorted in descending
            order
        :type order_by: list of (str, bool) tuples
        :param filters: a list of filters to apply
        :param filters: dict of field name and filter value combinations
        """
        limit_clause = 'LIMIT {}'.format(limit) if limit else ''
        order_by_clause = ''
        if order_by:
            l = []  # noqa: E741
            for field, desc in order_by:
                l.append(field + ' DESC' if desc else '')
            order_by_clause = 'ORDER BY ' + ', '.join(l)

        where_clause = ''
        if filters:
            l = []  # noqa: E741
            for field, value in filters.items():
                l.append("{field} = '{value}'".format(**locals()))
            where_clause = 'WHERE ' + ' AND '.join(l)

        sql = textwrap.dedent("""\
            SHOW PARTITIONS FROM {table_name}
            {where_clause}
            {order_by_clause}
            {limit_clause}
        """).format(**locals())
        return sql

    @classmethod
    def _latest_partition_from_df(cls, df):
        recs = df.to_records(index=False)
        if recs:
            return recs[0][0]

    @classmethod
    def latest_partition(cls, table_name, schema, database, show_first=False):
        """Returns col name and the latest (max) partition value for a table

        :param table_name: the name of the table
        :type table_name: str
        :param schema: schema / database / namespace
        :type schema: str
        :param database: database query will be run against
        :type database: models.Database
        :param show_first: displays the value for the first partitioning key
          if there are many partitioning keys
        :type show_first: bool

        >>> latest_partition('foo_table')
        '2018-01-01'
        """
        indexes = database.get_indexes(table_name, schema)
        if len(indexes[0]['column_names']) < 1:
            raise SupersetTemplateException(
                'The table should have one partitioned field')
        elif not show_first and len(indexes[0]['column_names']) > 1:
            raise SupersetTemplateException(
                'The table should have a single partitioned field '
                'to use this function. You may want to use '
                '`presto.latest_sub_partition`')
        part_field = indexes[0]['column_names'][0]
        sql = cls._partition_query(table_name, 1, [(part_field, True)])
        df = database.get_df(sql, schema)
        return part_field, cls._latest_partition_from_df(df)

    @classmethod
    def latest_sub_partition(cls, table_name, schema, database, **kwargs):
        """Returns the latest (max) partition value for a table

        A filtering criteria should be passed for all fields that are
        partitioned except for the field to be returned. For example,
        if a table is partitioned by (``ds``, ``event_type`` and
        ``event_category``) and you want the latest ``ds``, you'll want
        to provide a filter as keyword arguments for both
        ``event_type`` and ``event_category`` as in
        ``latest_sub_partition('my_table',
            event_category='page', event_type='click')``

        :param table_name: the name of the table, can be just the table
            name or a fully qualified table name as ``schema_name.table_name``
        :type table_name: str
        :param schema: schema / database / namespace
        :type schema: str
        :param database: database query will be run against
        :type database: models.Database

        :param kwargs: keyword arguments define the filtering criteria
            on the partition list. There can be many of these.
        :type kwargs: str
        >>> latest_sub_partition('sub_partition_table', event_type='click')
        '2018-01-01'
        """
        indexes = database.get_indexes(table_name, schema)
        part_fields = indexes[0]['column_names']
        for k in kwargs.keys():
            if k not in k in part_fields:
                msg = 'Field [{k}] is not part of the portioning key'
                raise SupersetTemplateException(msg)
        if len(kwargs.keys()) != len(part_fields) - 1:
            msg = (
                'A filter needs to be specified for {} out of the '
                '{} fields.'
            ).format(len(part_fields) - 1, len(part_fields))
            raise SupersetTemplateException(msg)

        for field in part_fields:
            if field not in kwargs.keys():
                field_to_return = field

        sql = cls._partition_query(
            table_name, 1, [(field_to_return, True)], kwargs)
        df = database.get_df(sql, schema)
        if df.empty:
            return ''
        return df.to_dict()[field_to_return][0]


class HiveEngineSpec(PrestoEngineSpec):

    """Reuses PrestoEngineSpec functionality."""

    engine = 'hive'

    # Scoping regex at class level to avoid recompiling
    # 17/02/07 19:36:38 INFO ql.Driver: Total jobs = 5
    jobs_stats_r = re.compile(
        r'.*INFO.*Total jobs = (?P<max_jobs>[0-9]+)')
    # 17/02/07 19:37:08 INFO ql.Driver: Launching Job 2 out of 5
    launching_job_r = re.compile(
        '.*INFO.*Launching Job (?P<job_number>[0-9]+) out of '
        '(?P<max_jobs>[0-9]+)')
    # 17/02/07 19:36:58 INFO exec.Task: 2017-02-07 19:36:58,152 Stage-18
    # map = 0%,  reduce = 0%
    stage_progress_r = re.compile(
        r'.*INFO.*Stage-(?P<stage_number>[0-9]+).*'
        r'map = (?P<map_progress>[0-9]+)%.*'
        r'reduce = (?P<reduce_progress>[0-9]+)%.*')

    @classmethod
    def patch(cls):
        from pyhive import hive
        from superset.db_engines import hive as patched_hive
        from TCLIService import (
            constants as patched_constants,
            ttypes as patched_ttypes,
            TCLIService as patched_TCLIService)

        hive.TCLIService = patched_TCLIService
        hive.constants = patched_constants
        hive.ttypes = patched_ttypes
        hive.Cursor.fetch_logs = patched_hive.fetch_logs

    @classmethod
    @cache_util.memoized_func(
        timeout=600,
        key=lambda *args, **kwargs: 'db:{}:{}'.format(args[0].id, args[1]))
    def fetch_result_sets(cls, db, datasource_type, force=False):
        return BaseEngineSpec.fetch_result_sets(
            db, datasource_type, force=force)

    @classmethod
    def fetch_data(cls, cursor, limit):
        from TCLIService import ttypes
        state = cursor.poll()
        if state.operationState == ttypes.TOperationState.ERROR_STATE:
            raise Exception('Query error', state.errorMessage)
        return super(HiveEngineSpec, cls).fetch_data(cursor, limit)

    @staticmethod
    def create_table_from_csv(form, table):
        """Uploads a csv file and creates a superset datasource in Hive."""
        def convert_to_hive_type(col_type):
            """maps tableschema's types to hive types"""
            tableschema_to_hive_types = {
                'boolean': 'BOOLEAN',
                'integer': 'INT',
                'number': 'DOUBLE',
                'string': 'STRING',
            }
            return tableschema_to_hive_types.get(col_type, 'STRING')

        table_name = form.name.data
        schema_name = form.schema.data

        if config.get('UPLOADED_CSV_HIVE_NAMESPACE'):
            if '.' in table_name or schema_name:
                raise Exception(
                    "You can't specify a namespace. "
                    'All tables will be uploaded to the `{}` namespace'.format(
                        config.get('HIVE_NAMESPACE')))
            table_name = '{}.{}'.format(
                config.get('UPLOADED_CSV_HIVE_NAMESPACE'), table_name)
        else:
            if '.' in table_name and schema_name:
                raise Exception(
                    "You can't specify a namespace both in the name of the table "
                    'and in the schema field. Please remove one')
            if schema_name:
                table_name = '{}.{}'.format(schema_name, table_name)

        filename = form.unirec_file.data
        bucket_path = config['CSV_TO_HIVE_UPLOAD_S3_BUCKET']

        if not bucket_path:
            logging.info('No upload bucket specified')
            raise Exception(
                'No upload bucket specified. You can specify one in the config file.')

        table_name = form.name.data
        filename = form.unirec_file.data
        upload_prefix = config['CSV_TO_HIVE_UPLOAD_DIRECTORY']

        upload_path = config['UNIREC_FOLDER'] + \
            secure_filename(form.unirec_file.data)

        hive_table_schema = Table(upload_path).infer()
        column_name_and_type = []
        for column_info in hive_table_schema['fields']:
            column_name_and_type.append(
                '{} {}'.format(
                    "'" + column_info['name'] + "'",
                    convert_to_hive_type(column_info['type'])))
        schema_definition = ', '.join(column_name_and_type)

        s3 = boto3.client('s3')
        location = os.path.join('s3a://', bucket_path, upload_prefix, table_name)
        s3.upload_file(
            upload_path, bucket_path,
            os.path.join(upload_prefix, table_name, filename))
        sql = """CREATE TABLE {table_name} ( {schema_definition} )
            ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS
            TEXTFILE LOCATION '{location}'
            tblproperties ('skip.header.line.count'='1')""".format(**locals())
        logging.info(form.con.data)
        engine = create_engine(form.con.data.sqlalchemy_uri_decrypted)
        engine.execute(sql)

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "CAST('{}' AS DATE)".format(dttm.isoformat()[:10])
        elif tt == 'TIMESTAMP':
            return "CAST('{}' AS TIMESTAMP)".format(
                dttm.strftime('%Y-%m-%d %H:%M:%S'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def adjust_database_uri(cls, uri, selected_schema=None):
        if selected_schema:
            uri.database = selected_schema
        return uri

    @classmethod
    def extract_error_message(cls, e):
        msg = str(e)
        match = re.search(r'errorMessage="(.*?)(?<!\\)"', msg)
        if match:
            msg = match.group(1)
        return msg

    @classmethod
    def progress(cls, log_lines):
        total_jobs = 1  # assuming there's at least 1 job
        current_job = 1
        stages = {}
        for line in log_lines:
            match = cls.jobs_stats_r.match(line)
            if match:
                total_jobs = int(match.groupdict()['max_jobs']) or 1
            match = cls.launching_job_r.match(line)
            if match:
                current_job = int(match.groupdict()['job_number'])
                total_jobs = int(match.groupdict()['max_jobs']) or 1
                stages = {}
            match = cls.stage_progress_r.match(line)
            if match:
                stage_number = int(match.groupdict()['stage_number'])
                map_progress = int(match.groupdict()['map_progress'])
                reduce_progress = int(match.groupdict()['reduce_progress'])
                stages[stage_number] = (map_progress + reduce_progress) / 2
        logging.info(
            'Progress detail: {}, '
            'current job {}, '
            'total jobs: {}'.format(stages, current_job, total_jobs))

        stage_progress = sum(
            stages.values()) / len(stages.values()) if stages else 0

        progress = (
            100 * (current_job - 1) / total_jobs + stage_progress / total_jobs
        )
        return int(progress)

    @classmethod
    def get_tracking_url(cls, log_lines):
        lkp = 'Tracking URL = '
        for line in log_lines:
            if lkp in line:
                return line.split(lkp)[1]

    @classmethod
    def handle_cursor(cls, cursor, query, session):
        """Updates progress information"""
        from pyhive import hive
        unfinished_states = (
            hive.ttypes.TOperationState.INITIALIZED_STATE,
            hive.ttypes.TOperationState.RUNNING_STATE,
        )
        polled = cursor.poll()
        last_log_line = 0
        tracking_url = None
        job_id = None
        while polled.operationState in unfinished_states:
            query = session.query(type(query)).filter_by(id=query.id).one()
            if query.status == QueryStatus.STOPPED:
                cursor.cancel()
                break

            log = cursor.fetch_logs() or ''
            if log:
                log_lines = log.splitlines()
                progress = cls.progress(log_lines)
                logging.info('Progress total: {}'.format(progress))
                needs_commit = False
                if progress > query.progress:
                    query.progress = progress
                    needs_commit = True
                if not tracking_url:
                    tracking_url = cls.get_tracking_url(log_lines)
                    if tracking_url:
                        job_id = tracking_url.split('/')[-2]
                        logging.info(
                            'Found the tracking url: {}'.format(tracking_url))
                        tracking_url = tracking_url_trans(tracking_url)
                        logging.info(
                            'Transformation applied: {}'.format(tracking_url))
                        query.tracking_url = tracking_url
                        logging.info('Job id: {}'.format(job_id))
                        needs_commit = True
                if job_id and len(log_lines) > last_log_line:
                    # Wait for job id before logging things out
                    # this allows for prefixing all log lines and becoming
                    # searchable in something like Kibana
                    for l in log_lines[last_log_line:]:
                        logging.info('[{}] {}'.format(job_id, l))
                    last_log_line = len(log_lines)
                if needs_commit:
                    session.commit()
            time.sleep(hive_poll_interval)
            polled = cursor.poll()

    @classmethod
    def where_latest_partition(
            cls, table_name, schema, database, qry, columns=None):
        try:
            col_name, value = cls.latest_partition(
                table_name, schema, database)
        except Exception:
            # table is not partitioned
            return False
        for c in columns:
            if str(c.name) == str(col_name):
                return qry.where(c == str(value))
        return False

    @classmethod
    def latest_sub_partition(cls, table_name, schema, database, **kwargs):
        # TODO(bogdan): implement`
        pass

    @classmethod
    def _latest_partition_from_df(cls, df):
        """Hive partitions look like ds={partition name}"""
        return df.ix[:, 0].max().split('=')[1]

    @classmethod
    def _partition_query(
            cls, table_name, limit=0, order_by=None, filters=None):
        return 'SHOW PARTITIONS {table_name}'.format(**locals())

    @classmethod
    def modify_url_for_impersonation(cls, url, impersonate_user, username):
        """
        Modify the SQL Alchemy URL object with the user to impersonate if applicable.
        :param url: SQLAlchemy URL object
        :param impersonate_user: Bool indicating if impersonation is enabled
        :param username: Effective username
        """
        # Do nothing in the URL object since instead this should modify
        # the configuraiton dictionary. See get_configuration_for_impersonation
        pass

    @classmethod
    def get_configuration_for_impersonation(cls, uri, impersonate_user, username):
        """
        Return a configuration dictionary that can be merged with other configs
        that can set the correct properties for impersonating users
        :param uri: URI string
        :param impersonate_user: Bool indicating if impersonation is enabled
        :param username: Effective username
        :return: Dictionary with configs required for impersonation
        """
        configuration = {}
        url = make_url(uri)
        backend_name = url.get_backend_name()

        # Must be Hive connection, enable impersonation, and set param auth=LDAP|KERBEROS
        if (backend_name == 'hive' and 'auth' in url.query.keys() and
                impersonate_user is True and username is not None):
            configuration['hive.server2.proxy.user'] = username
        return configuration

    @staticmethod
    def execute(cursor, query, async=False):
        cursor.execute(query, async=async)


class MssqlEngineSpec(BaseEngineSpec):
    engine = 'mssql'
    epoch_to_dttm = "dateadd(S, {col}, '1970-01-01')"
    limit_method = LimitMethod.WRAP_SQL

    time_grain_functions = {
        None: '{col}',
        'PT1S': "DATEADD(second, DATEDIFF(second, '2000-01-01', {col}), '2000-01-01')",
        'PT1M': 'DATEADD(minute, DATEDIFF(minute, 0, {col}), 0)',
        'PT5M': 'DATEADD(minute, DATEDIFF(minute, 0, {col}) / 5 * 5, 0)',
        'PT10M': 'DATEADD(minute, DATEDIFF(minute, 0, {col}) / 10 * 10, 0)',
        'PT15M': 'DATEADD(minute, DATEDIFF(minute, 0, {col}) / 15 * 15, 0)',
        'PT0.5H': 'DATEADD(minute, DATEDIFF(minute, 0, {col}) / 30 * 30, 0)',
        'PT1H': 'DATEADD(hour, DATEDIFF(hour, 0, {col}), 0)',
        'P1D': 'DATEADD(day, DATEDIFF(day, 0, {col}), 0)',
        'P1W': 'DATEADD(week, DATEDIFF(week, 0, {col}), 0)',
        'P1M': 'DATEADD(month, DATEDIFF(month, 0, {col}), 0)',
        'P0.25Y': 'DATEADD(quarter, DATEDIFF(quarter, 0, {col}), 0)',
        'P1Y': 'DATEADD(year, DATEDIFF(year, 0, {col}), 0)',
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        return "CONVERT(DATETIME, '{}', 126)".format(dttm.isoformat())


class AthenaEngineSpec(BaseEngineSpec):
    engine = 'awsathena'

    time_grain_functions = {
        None: '{col}',
        'PT1S': "date_trunc('second', CAST({col} AS TIMESTAMP))",
        'PT1M': "date_trunc('minute', CAST({col} AS TIMESTAMP))",
        'PT1H': "date_trunc('hour', CAST({col} AS TIMESTAMP))",
        'P1D': "date_trunc('day', CAST({col} AS TIMESTAMP))",
        'P1W': "date_trunc('week', CAST({col} AS TIMESTAMP))",
        'P1M': "date_trunc('month', CAST({col} AS TIMESTAMP))",
        'P0.25Y': "date_trunc('quarter', CAST({col} AS TIMESTAMP))",
        'P1Y': "date_trunc('year', CAST({col} AS TIMESTAMP))",
        'P1W/1970-01-03T00:00:00Z': "date_add('day', 5, date_trunc('week', \
                                    date_add('day', 1, CAST({col} AS TIMESTAMP))))",
        '1969-12-28T00:00:00Z/P1W': "date_add('day', -1, date_trunc('week', \
                                    date_add('day', 1, CAST({col} AS TIMESTAMP))))",
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "from_iso8601_date('{}')".format(dttm.isoformat()[:10])
        if tt == 'TIMESTAMP':
            return "from_iso8601_timestamp('{}')".format(dttm.isoformat())
        return ("CAST ('{}' AS TIMESTAMP)"
                .format(dttm.strftime('%Y-%m-%d %H:%M:%S')))

    @classmethod
    def epoch_to_dttm(cls):
        return 'from_unixtime({col})'


class ClickHouseEngineSpec(BaseEngineSpec):
    """Dialect for ClickHouse analytical DB."""

    engine = 'clickhouse'

    time_secondary_columns = True
    time_groupby_inline = True

    time_grain_functions = {
        None: '{col}',
        'PT1M': 'toStartOfMinute(toDateTime({col}))',
        'PT5M': 'toDateTime(intDiv(toUInt32(toDateTime({col})), 300)*300)',
        'PT10M': 'toDateTime(intDiv(toUInt32(toDateTime({col})), 600)*600)',
        'PT15M': 'toDateTime(intDiv(toUInt32(toDateTime({col})), 900)*900)',
        'PT0.5H': 'toDateTime(intDiv(toUInt32(toDateTime({col})), 1800)*1800)',
        'PT1H': 'toStartOfHour(toDateTime({col}))',
        'P1D': 'toStartOfDay(toDateTime({col}))',
        'P1W': 'toMonday(toDateTime({col}))',
        'P1M': 'toStartOfMonth(toDateTime({col}))',
        'P0.25Y': 'toStartOfQuarter(toDateTime({col}))',
        'P1Y': 'toStartOfYear(toDateTime({col}))',
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "toDate('{}')".format(dttm.strftime('%Y-%m-%d'))
        if tt == 'DATETIME':
            return "toDateTime('{}')".format(
                dttm.strftime('%Y-%m-%d %H:%M:%S'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))


class BQEngineSpec(BaseEngineSpec):
    """Engine spec for Google's BigQuery

    As contributed by @mxmzdlv on issue #945"""
    engine = 'bigquery'

    """
    https://www.python.org/dev/peps/pep-0249/#arraysize
    raw_connections bypass the pybigquery query execution context and deal with
    raw dbapi connection directly.
    If this value is not set, the default value is set to 1, as described here,
    https://googlecloudplatform.github.io/google-cloud-python/latest/_modules/google/cloud/bigquery/dbapi/cursor.html#Cursor

    The default value of 5000 is derived from the pybigquery.
    https://github.com/mxmzdlv/pybigquery/blob/d214bb089ca0807ca9aaa6ce4d5a01172d40264e/pybigquery/sqlalchemy_bigquery.py#L102
    """
    arraysize = 5000

    time_grain_functions = {
        None: '{col}',
        'PT1S': 'TIMESTAMP_TRUNC({col}, SECOND)',
        'PT1M': 'TIMESTAMP_TRUNC({col}, MINUTE)',
        'PT1H': 'TIMESTAMP_TRUNC({col}, HOUR)',
        'P1D': 'TIMESTAMP_TRUNC({col}, DAY)',
        'P1W': 'TIMESTAMP_TRUNC({col}, WEEK)',
        'P1M': 'TIMESTAMP_TRUNC({col}, MONTH)',
        'P0.25Y': 'TIMESTAMP_TRUNC({col}, QUARTER)',
        'P1Y': 'TIMESTAMP_TRUNC({col}, YEAR)',
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "'{}'".format(dttm.strftime('%Y-%m-%d'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def fetch_data(cls, cursor, limit):
        data = super(BQEngineSpec, cls).fetch_data(cursor, limit)
        if len(data) != 0 and type(data[0]).__name__ == 'Row':
            data = [r.values() for r in data]
        return data

    @classmethod
    def _get_fields(cls, cols):
        """
        BigQuery dialect requires us to not use backtick in the fieldname which are
        nested.
        Using literal_column handles that issue.
        http://docs.sqlalchemy.org/en/latest/core/tutorial.html#using-more-specific-text-with-table-literal-column-and-column
        Also explicility specifying column names so we don't encounter duplicate
        column names in the result.
        """
        return [sqla.literal_column(c.get('name')).label(c.get('name').replace('.', '__'))
                for c in cols]


class ImpalaEngineSpec(BaseEngineSpec):
    """Engine spec for Cloudera's Impala"""

    engine = 'impala'

    time_grain_functions = {
        None: '{col}',
        'PT1M': "TRUNC({col}, 'MI')",
        'PT1H': "TRUNC({col}, 'HH')",
        'P1D': "TRUNC({col}, 'DD')",
        'P1W': "TRUNC({col}, 'WW')",
        'P1M': "TRUNC({col}, 'MONTH')",
        'P0.25Y': "TRUNC({col}, 'Q')",
        'P1Y': "TRUNC({col}, 'YYYY')",
    }

    @classmethod
    def epoch_to_dttm(cls):
        return 'from_unixtime({col})'

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "'{}'".format(dttm.strftime('%Y-%m-%d'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def get_schema_names(cls, inspector):
        schemas = [row[0] for row in inspector.engine.execute('SHOW SCHEMAS')
                   if not row[0].startswith('_')]
        return schemas


class DruidEngineSpec(BaseEngineSpec):
    """Engine spec for Druid.io"""
    engine = 'druid'
    inner_joins = False
    allows_subquery = False

    time_grain_functions = {
        None: '{col}',
        'PT1S': 'FLOOR({col} TO SECOND)',
        'PT1M': 'FLOOR({col} TO MINUTE)',
        'PT1H': 'FLOOR({col} TO HOUR)',
        'P1D': 'FLOOR({col} TO DAY)',
        'P1W': 'FLOOR({col} TO WEEK)',
        'P1M': 'FLOOR({col} TO MONTH)',
        'P0.25Y': 'FLOOR({col} TO QUARTER)',
        'P1Y': 'FLOOR({col} TO YEAR)',
    }


class KylinEngineSpec(BaseEngineSpec):
    """Dialect for Apache Kylin"""

    engine = 'kylin'

    time_grain_functions = {
        None: '{col}',
        'PT1S': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO SECOND) AS TIMESTAMP)',
        'PT1M': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO MINUTE) AS TIMESTAMP)',
        'PT1H': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO HOUR) AS TIMESTAMP)',
        'P1D': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO DAY) AS DATE)',
        'P1W': 'CAST(TIMESTAMPADD(WEEK, WEEK(CAST({col} AS DATE)) - 1, \
               FLOOR(CAST({col} AS TIMESTAMP) TO YEAR)) AS DATE)',
        'P1M': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO MONTH) AS DATE)',
        'P0.25Y': 'CAST(TIMESTAMPADD(QUARTER, QUARTER(CAST({col} AS DATE)) - 1, \
                  FLOOR(CAST({col} AS TIMESTAMP) TO YEAR)) AS DATE)',
        'P1Y': 'CAST(FLOOR(CAST({col} AS TIMESTAMP) TO YEAR) AS DATE)',
    }

    @classmethod
    def convert_dttm(cls, target_type, dttm):
        tt = target_type.upper()
        if tt == 'DATE':
            return "CAST('{}' AS DATE)".format(dttm.isoformat()[:10])
        if tt == 'TIMESTAMP':
            return "CAST('{}' AS TIMESTAMP)".format(
                dttm.strftime('%Y-%m-%d %H:%M:%S'))
        return "'{}'".format(dttm.strftime('%Y-%m-%d %H:%M:%S'))


engines = {
    o.engine: o for o in globals().values()
    if inspect.isclass(o) and issubclass(o, BaseEngineSpec)}
