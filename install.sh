#!/bin/sh
# fields
#path_coliot = /opt/coliotjj

# Package list
apt-get update

# Install dependencies Debian and Ubuntu
apt-get install build-essential libssl-dev libffi-dev python-dev python-pip libsasl2-dev libldap2-dev -y
# Ubuntu 16.04 LTS -add python3.5-dev

# Install SQLite3
apt-get install sqlite3

apt-get install mysql-server -y
apt-get install libmysqlclient-dev -y

sudo apt install nodejs npm -y

# Python’s setup tools and pip
pip3 install --upgrade setuptools pip

pip3 install Flask-Compress

pip3 install python-dotenv

pip3 install virtualenv 

pip3 install Flask==1.0

pip3 install "markdown<3.0.0" superset

pip install psycopg2 -binary

# Superset installation and initialization

# Create directory
mkdir -p /opt/coliot

git clone https://github.com/apache/incubator-superset.git -b 0.26.0 /opt/coliot/
#etc.

# Move to dir
#cd /opt/coliot/

# Flask server
# Create a virtual environemnt and activate it (recommended)
#virtualenv -p python3 venv . # setup a python3.6 virtualenv
#source venv/bin/activate

# Install external dependencies
pip3 install -r /opt/coliot/requirements.txt
pip3 install -r /opt/coliot/requirements-dev.txt
# Install Superset in editable (development) mode
pip3 install -e /opt/coliot/.

# Create an admin user
fabmanager create-admin --app superset

# Initialize the database
superset db upgrade

# Create default roles and permissions
superset init

# Load some data to play with
superset load_examples

# Start the Flask dev web server from inside the `superset` dir at port 8088
# Note that your page may not have css at this point.
# See instructions below how to build the front-end assets.

rm -R /opt/coliot/superset
cp -R ./collector /opt/coliot/superset


cd /opt/coliot/superset/assets
npm run build
#FLASK_ENV=development flask run -p 8088 --with-threads --reload --debugger
