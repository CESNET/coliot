(window.webpackJsonp=window.webpackJsonp||[]).push([[35],{1797:function(t,a,n){"use strict";var e=i(n(2694));n(2696);var o=i(n(22)),r=n(31);function i(t){return t&&t.__esModule?t:{default:t}}n(2784),(0,e.default)(window,o.default),t.exports=function(t,a){var n=t.container,e=t.formData,i=n.height(),d=a.data.columns;Array.isArray(d[0])&&(d=d.map(function(t){return t[0]})),n.html(a.data.html);var s=function(){return function(){var a=(0,o.default)(this)[0].textContent;(0,o.default)(this)[0].textContent=t.datasource.verbose_map[a]||a}}();(t.container.find("thead tr:first th").each(s),t.container.find("thead tr th:first-child").each(s),t.container.find("tbody tr").each(function(){(0,o.default)(this).find("td").each(function(a){var n=d[a],i=t.datasource.column_formats[n]||e.number_format||".3s",s=(0,o.default)(this)[0].textContent;isNaN(s)||""===s||((0,o.default)(this)[0].textContent=(0,r.d3format)(i,s))})}),1===e.groupby.length)?(n.css("overflow","hidden"),n.find("table").DataTable({paging:!1,searching:!1,bInfo:!1,scrollY:i+"px",scrollCollapse:!0,scrollX:!0}).column("-1").order("desc").draw(),(0,r.fixDataTableBodyHeight)(n.find(".dataTables_wrapper"),i)):(n.css("overflow","auto"),n.css("height",i+10+"px"))}},2784:function(t,a,n){}}]);