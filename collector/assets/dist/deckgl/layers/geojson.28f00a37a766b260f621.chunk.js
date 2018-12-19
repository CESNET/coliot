(window.webpackJsonp=window.webpackJsonp||[]).push([[52],{1189:function(t,e,o){"use strict";var r=c(o(1)),n=c(o(15)),i=o(2573),a=c(o(2575)),u=function(t){if(t&&t.__esModule)return t;var e={};if(null!=t)for(var o in t)Object.prototype.hasOwnProperty.call(t,o)&&(e[o]=t[o]);return e.default=t,e}(o(2576)),s=o(240),l=c(o(608));function c(t){return t&&t.__esModule?t:{default:t}}var f={fillColor:"fillColor",color:"fillColor",fill:"fillColor","fill-color":"fillColor",strokeColor:"strokeColor","stroke-color":"strokeColor","stroke-width":"strokeWidth"},d=function(){return function(t,e){var o={};return Object.keys(t).forEach(function(e){e in f?o[f[e]]=t[e]:o[e]=t[e]}),"string"==typeof t.fillColor&&(o.fillColor=(0,s.hexToRGB)(p.fillColor)),"string"==typeof t.strokeColor&&(o.strokeColor=(0,s.hexToRGB)(p.strokeColor)),Object.assign({},o,e)}}(),h=void 0,v=function(){return function t(e,o,r){if(e&&e.features&&e.features.forEach(function(n){t(n,o,e.extraProps||r)}),e&&e.geometry){var n=Object.assign({},e,{properties:d(e.properties,o)});n.extraProps||(n.extraProps=r),h.push(n)}}}();function y(t,e,o){var r=t,n=r.fill_color_picker,a=r.stroke_color_picker,s=[n.r,n.g,n.b,255*n.a],c=[a.r,a.g,a.b,255*a.a],f={};s[3]>0&&(f.fillColor=s),c[3]>0&&(f.strokeColor=c),h=[],v(e.data,f);var p=void 0;return r.js_data_mutator&&(p=(0,l.default)(r.js_data_mutator),h=p(h)),new i.GeoJsonLayer(Object.assign({id:"geojson-layer-"+r.slice_id,filled:r.filled,data:h,stroked:r.stroked,extruded:r.extruded,pointRadiusScale:r.point_radius_scale},u.commonLayerProps(r,o)))}t.exports={default:function(t,e,o){var i=y(t.formData,e,t),u=Object.assign({},t.formData.viewport,{width:t.width(),height:t.height()});t.formData.autozoom,n.default.render(r.default.createElement(a.default,{mapboxApiAccessToken:e.data.mapboxApiKey,viewport:u,layers:[i],mapStyle:t.formData.mapbox_style,setControlValue:o}),document.getElementById(t.containerId))},getLayer:y}},2575:function(t,e,o){"use strict";Object.defineProperty(e,"__esModule",{value:!0});var r=Object.assign||function(t){for(var e=1;e<arguments.length;e++){var o=arguments[e];for(var r in o)Object.prototype.hasOwnProperty.call(o,r)&&(t[r]=o[r])}return t},n=function(){function t(t,e){for(var o=0;o<e.length;o++){var r=e[o];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,r.key,r)}}return function(e,o,r){return o&&t(e.prototype,o),r&&t(e,r),e}}(),i=l(o(1)),a=l(o(0)),u=l(o(2583)),s=l(o(2573));function l(t){return t&&t.__esModule?t:{default:t}}o(2584);var c={viewport:a.default.object.isRequired,layers:a.default.array.isRequired,setControlValue:a.default.func.isRequired,mapStyle:a.default.string,mapboxApiAccessToken:a.default.string.isRequired,onViewportChange:a.default.func},f={mapStyle:"light",onViewportChange:function(){return function(){}}()},p=function(t){function e(t){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,e);var o=function(t,e){if(!t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!e||"object"!=typeof e&&"function"!=typeof e?t:e}(this,(e.__proto__||Object.getPrototypeOf(e)).call(this,t));return o.state={viewport:t.viewport},o.tick=o.tick.bind(o),o.onViewportChange=o.onViewportChange.bind(o),o}return function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function, not "+typeof e);t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,enumerable:!1,writable:!0,configurable:!0}}),e&&(Object.setPrototypeOf?Object.setPrototypeOf(t,e):t.__proto__=e)}(e,i["default"].Component),n(e,[{key:"componentWillMount",value:function(){return function(){var t=setInterval(this.tick,1e3);this.setState(function(){return{timer:t}})}}()},{key:"componentWillReceiveProps",value:function(){return function(t){var e=this;this.setState(function(){return{viewport:Object.assign({},t.viewport),previousViewport:e.state.viewport}})}}()},{key:"componentWillUnmount",value:function(){return function(){this.clearInterval(this.state.timer)}}()},{key:"onViewportChange",value:function(){return function(t){var e=Object.assign({},t);delete e.width,delete e.height;var o=Object.assign({},this.state.viewport,e);this.setState(function(){return{viewport:o}}),this.props.onViewportChange(o)}}()},{key:"tick",value:function(){return function(){var t=this;if(this.state.previousViewport!==this.state.viewport){var e=this.props.setControlValue,o=this.state.viewport;e&&e("viewport",o),this.setState(function(){return{previousViewport:t.state.viewport}})}}}()},{key:"layers",value:function(){return function(){return this.props.layers.some(function(t){return"function"==typeof t})?this.props.layers.map(function(t){return"function"==typeof t?t():t}):this.props.layers}}()},{key:"render",value:function(){return function(){var t=this.state.viewport;return i.default.createElement(u.default,r({},t,{mapStyle:this.props.mapStyle,onViewportChange:this.onViewportChange,mapboxApiAccessToken:this.props.mapboxApiAccessToken}),i.default.createElement(s.default,r({},t,{layers:this.layers(),initWebGLParameters:!0})))}}()}]),e}();e.default=p,p.propTypes=c,p.defaultProps=f},2576:function(t,e,o){"use strict";Object.defineProperty(e,"__esModule",{value:!0}),e.getBounds=u,e.fitViewport=function(t,e){var o=arguments.length>2&&void 0!==arguments[2]?arguments[2]:10;try{var r=u(e);return Object.assign({},t,(0,n.fitBounds)({height:t.height,width:t.width,padding:o,bounds:r}))}catch(e){return console.error("Could not auto zoom",e),t}},e.commonLayerProps=function(t,e){var o=t,n=void 0;if(o.js_tooltip){var a=(0,i.default)(o.js_tooltip);n=function(){return function(t){t.picked?e.setTooltip({content:r.default.sanitize(a(t)),x:t.x,y:t.y}):e.setTooltip(null)}}()}var u=void 0;o.js_onclick_href&&(u=function(){return function(t){var e=(0,i.default)(o.js_onclick_href)(t);window.open(e)}}());return{onClick:u,onHover:n,pickable:Boolean(n)}};var r=a(o(2580)),n=o(2578),i=a(o(608));function a(t){return t&&t.__esModule?t:{default:t}}function u(t){var e=d3.extent(t,function(t){return t[1]}),o=d3.extent(t,function(t){return t[0]});return[[o[0],e[0]],[o[1],e[1]]]}}}]);