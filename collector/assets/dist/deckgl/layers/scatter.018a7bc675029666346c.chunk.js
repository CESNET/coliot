(window.webpackJsonp=window.webpackJsonp||[]).push([[47],{1184:function(e,t,r){"use strict";var n=function(){function e(e,t){for(var r=0;r<t.length;r++){var n=t[r];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,n.key,n)}}return function(t,r,n){return r&&e(t.prototype,r),n&&e(t,n),t}}(),o=v(r(1)),a=v(r(15)),i=v(r(0)),u=r(2573),s=v(r(2601)),l=v(r(2650)),c=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&(t[r]=e[r]);return t.default=e,t}(r(2576)),f=r(240),p=r(2602),d=r(409),h=v(r(608));function v(e){return e&&e.__esModule?e:{default:e}}function y(e,t,r,n){var o=e,a=o.color_picker||{r:0,g:0,b:0,a:1},i=[a.r,a.g,a.b,255*a.a],s=t.data.features.map(function(e){var t=(0,d.unitToRadius)(o.point_unit,e.radius)||10;o.multiplier&&(t*=o.multiplier);var r=void 0;return r=o.dimension?(0,f.hexToRGB)((0,f.getColorFromScheme)(e.cat_color,o.color_scheme),255*a.a):i,Object.assign({},e,{radius:t,color:r})});if(o.js_data_mutator){var l=(0,h.default)(o.js_data_mutator);s=l(s)}return null!=n&&n.forEach(function(e){s=s.filter(e)}),new u.ScatterplotLayer(Object.assign({id:"scatter-layer-"+o.slice_id,data:s,fp64:!0,radiusMinPixels:o.min_radius||null,radiusMaxPixels:o.max_radius||null,outline:!1},c.commonLayerProps(o,r)))}var b={slice:i.default.object.isRequired,payload:i.default.object.isRequired,setControlValue:i.default.func.isRequired,viewport:i.default.object.isRequired},m=function(e){function t(e){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t);var r=function(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}(this,(t.__proto__||Object.getPrototypeOf(t)).call(this,e));return r.state=t.getDerivedStateFromProps(e),r.getLayers=r.getLayers.bind(r),r.toggleCategory=r.toggleCategory.bind(r),r.showSingleCategory=r.showSingleCategory.bind(r),r}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,o["default"].PureComponent),n(t,null,[{key:"getDerivedStateFromProps",value:function(){return function(e){var t=e.slice.formData,r=t.time_grain_sqla||t.granularity||"PT1M",n=e.payload.data.features.map(function(e){return e.__timestamp}),o=(0,p.getPlaySliderParams)(n,r);return{start:o.start,end:o.end,step:o.step,values:o.values,disabled:o.disabled,categories:function(e,t){var r=e,n=r.color_picker||{r:0,g:0,b:0,a:1},o=[n.r,n.g,n.b,255*n.a],a={};return t.data.features.forEach(function(e){if(null!=e.cat_color&&!a.hasOwnProperty(e.cat_color)){var t=void 0;t=r.dimension?(0,f.hexToRGB)((0,f.getColorFromScheme)(e.cat_color,r.color_scheme),255*n.a):o,a[e.cat_color]={color:t,enabled:!0}}}),a}(t,e.payload)}}}()}]),n(t,[{key:"componentWillReceiveProps",value:function(){return function(e){this.setState(t.getDerivedStateFromProps(e,this.state))}}()},{key:"getLayers",value:function(){return function(e){var t=this,r=[];return e[0]===e[1]||e[1]===this.end?r.push(function(t){return t.__timestamp>=e[0]&&t.__timestamp<=e[1]}):r.push(function(t){return t.__timestamp>=e[0]&&t.__timestamp<e[1]}),this.props.slice.formData.dimension&&r.push(function(e){return t.state.categories[e.cat_color].enabled}),[y(this.props.slice.formData,this.props.payload,this.props.slice,r)]}}()},{key:"toggleCategory",value:function(){return function(e){var t=this.state.categories[e];t.enabled=!t.enabled;var r=Object.assign({},this.state.categories,function(e,t,r){return t in e?Object.defineProperty(e,t,{value:r,enumerable:!0,configurable:!0,writable:!0}):e[t]=r,e}({},e,t));Object.values(r).every(function(e){return!e.enabled})&&Object.values(r).forEach(function(e){e.enabled=!0}),this.setState({categories:r})}}()},{key:"showSingleCategory",value:function(){return function(e){var t=Object.assign({},this.state.categories);Object.values(t).forEach(function(e){e.enabled=!1}),t[e].enabled=!0,this.setState({categories:t})}}()},{key:"render",value:function(){return function(){return o.default.createElement("div",null,o.default.createElement(s.default,{getLayers:this.getLayers,start:this.state.start,end:this.state.end,step:this.state.step,values:this.state.values,disabled:this.state.disabled,viewport:this.props.viewport,mapboxApiAccessToken:this.props.payload.data.mapboxApiKey,mapStyle:this.props.slice.formData.mapbox_style,setControlValue:this.props.setControlValue},o.default.createElement(l.default,{categories:this.state.categories,toggleCategory:this.toggleCategory,showSingleCategory:this.showSingleCategory,position:this.props.slice.formData.legend_position})))}}()}]),t}();m.propTypes=b,e.exports={default:function(e,t,r){var n=e.formData,i=Object.assign({},n.viewport,{width:e.width(),height:e.height()});n.autozoom&&(i=c.fitViewport(i,function(e){return e.map(function(e){return e.position})}(t.data.features))),a.default.render(o.default.createElement(m,{slice:e,payload:t,setControlValue:r,viewport:i}),document.getElementById(e.containerId))},getLayer:y}},2575:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var n=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var n in r)Object.prototype.hasOwnProperty.call(r,n)&&(e[n]=r[n])}return e},o=function(){function e(e,t){for(var r=0;r<t.length;r++){var n=t[r];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,n.key,n)}}return function(t,r,n){return r&&e(t.prototype,r),n&&e(t,n),t}}(),a=l(r(1)),i=l(r(0)),u=l(r(2583)),s=l(r(2573));function l(e){return e&&e.__esModule?e:{default:e}}r(2584);var c={viewport:i.default.object.isRequired,layers:i.default.array.isRequired,setControlValue:i.default.func.isRequired,mapStyle:i.default.string,mapboxApiAccessToken:i.default.string.isRequired,onViewportChange:i.default.func},f={mapStyle:"light",onViewportChange:function(){return function(){}}()},p=function(e){function t(e){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t);var r=function(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}(this,(t.__proto__||Object.getPrototypeOf(t)).call(this,e));return r.state={viewport:e.viewport},r.tick=r.tick.bind(r),r.onViewportChange=r.onViewportChange.bind(r),r}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,a["default"].Component),o(t,[{key:"componentWillMount",value:function(){return function(){var e=setInterval(this.tick,1e3);this.setState(function(){return{timer:e}})}}()},{key:"componentWillReceiveProps",value:function(){return function(e){var t=this;this.setState(function(){return{viewport:Object.assign({},e.viewport),previousViewport:t.state.viewport}})}}()},{key:"componentWillUnmount",value:function(){return function(){this.clearInterval(this.state.timer)}}()},{key:"onViewportChange",value:function(){return function(e){var t=Object.assign({},e);delete t.width,delete t.height;var r=Object.assign({},this.state.viewport,t);this.setState(function(){return{viewport:r}}),this.props.onViewportChange(r)}}()},{key:"tick",value:function(){return function(){var e=this;if(this.state.previousViewport!==this.state.viewport){var t=this.props.setControlValue,r=this.state.viewport;t&&t("viewport",r),this.setState(function(){return{previousViewport:e.state.viewport}})}}}()},{key:"layers",value:function(){return function(){return this.props.layers.some(function(e){return"function"==typeof e})?this.props.layers.map(function(e){return"function"==typeof e?e():e}):this.props.layers}}()},{key:"render",value:function(){return function(){var e=this.state.viewport;return a.default.createElement(u.default,n({},e,{mapStyle:this.props.mapStyle,onViewportChange:this.onViewportChange,mapboxApiAccessToken:this.props.mapboxApiAccessToken}),a.default.createElement(s.default,n({},e,{layers:this.layers(),initWebGLParameters:!0})))}}()}]),t}();t.default=p,p.propTypes=c,p.defaultProps=f},2576:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.getBounds=u,t.fitViewport=function(e,t){var r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:10;try{var n=u(t);return Object.assign({},e,(0,o.fitBounds)({height:e.height,width:e.width,padding:r,bounds:n}))}catch(t){return console.error("Could not auto zoom",t),e}},t.commonLayerProps=function(e,t){var r=e,o=void 0;if(r.js_tooltip){var i=(0,a.default)(r.js_tooltip);o=function(){return function(e){e.picked?t.setTooltip({content:n.default.sanitize(i(e)),x:e.x,y:e.y}):t.setTooltip(null)}}()}var u=void 0;r.js_onclick_href&&(u=function(){return function(e){var t=(0,a.default)(r.js_onclick_href)(e);window.open(t)}}());return{onClick:u,onHover:o,pickable:Boolean(o)}};var n=i(r(2580)),o=r(2578),a=i(r(608));function i(e){return e&&e.__esModule?e:{default:e}}function u(e){var t=d3.extent(e,function(e){return e[1]}),r=d3.extent(e,function(e){return e[0]});return[[r[0],t[0]],[r[1],t[1]]]}},2601:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var n=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var n in r)Object.prototype.hasOwnProperty.call(r,n)&&(e[n]=r[n])}return e},o=function(){function e(e,t){for(var r=0;r<t.length;r++){var n=t[r];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,n.key,n)}}return function(t,r,n){return r&&e(t.prototype,r),n&&e(t,n),t}}(),a=l(r(1)),i=l(r(0)),u=l(r(2575)),s=l(r(2611));function l(e){return e&&e.__esModule?e:{default:e}}var c={getLayers:i.default.func.isRequired,start:i.default.number.isRequired,end:i.default.number.isRequired,step:i.default.number.isRequired,values:i.default.array.isRequired,disabled:i.default.bool,viewport:i.default.object.isRequired,children:i.default.node},f=function(e){function t(e){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t);var r=function(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}(this,(t.__proto__||Object.getPrototypeOf(t)).call(this,e)),n=(e.getLayers,e.start,e.end,e.step,e.values),o=(e.disabled,e.viewport),a=function(e,t){var r={};for(var n in e)t.indexOf(n)>=0||Object.prototype.hasOwnProperty.call(e,n)&&(r[n]=e[n]);return r}(e,["getLayers","start","end","step","values","disabled","viewport"]);return r.state={values:n,viewport:o},r.other=a,r}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,a["default"].Component),o(t,[{key:"componentWillReceiveProps",value:function(){return function(e){this.setState({values:e.values,viewport:e.viewport})}}()},{key:"render",value:function(){return function(){var e=this,t=this.props.getLayers(this.state.values);return a.default.createElement("div",null,a.default.createElement(u.default,n({},this.other,{viewport:this.state.viewport,layers:t,onViewportChange:function(t){return e.setState({viewport:t})}})),!this.props.disabled&&a.default.createElement(s.default,{start:this.props.start,end:this.props.end,step:this.props.step,values:this.state.values,onChange:function(t){return e.setState({values:t})}}),this.props.children)}}()}]),t}();t.default=f,f.propTypes=c,f.defaultProps={disabled:!1,step:1}},2602:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.getPlaySliderParams=void 0;var n=function(e){return e&&e.__esModule?e:{default:e}}(r(2653));function o(e){if(Array.isArray(e)){for(var t=0,r=Array(e.length);t<e.length;t++)r[t]=e[t];return r}return Array.from(e)}t.getPlaySliderParams=function(){return function(e,t){var r=Math.min.apply(Math,o(e)),a=Math.max.apply(Math,o(e)),i=void 0;if(t.indexOf("/")>0){var u=t.split("/",2),s=void 0;u[0].endsWith("Z")?(s=new Date(u[0]).getTime(),i=(0,n.default)(u[1])):(s=new Date(u[1]).getTime(),i=(0,n.default)(u[0])),r=s+i*Math.floor((r-s)/i),a=s+i*(Math.floor((a-s)/i)+1)}else r-=r%(i=(0,n.default)(t)),a+=i-a%i;return{start:r,end:a,step:i,values:null!=t?[r,r+i]:[r,a],disabled:e.every(function(e){return null===e})}}}()},2611:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var n=function(){function e(e,t){for(var r=0;r<t.length;r++){var n=t[r];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,n.key,n)}}return function(t,r,n){return r&&e(t.prototype,r),n&&e(t,n),t}}(),o=c(r(1)),a=c(r(0)),i=r(12),u=c(r(1181));r(2648);var s=c(r(2649));r(2612);var l=r(11);function c(e){return e&&e.__esModule?e:{default:e}}var f={start:a.default.number.isRequired,step:a.default.number.isRequired,end:a.default.number.isRequired,values:a.default.array.isRequired,onChange:a.default.func,loopDuration:a.default.number,maxFrames:a.default.number,orientation:a.default.oneOf(["horizontal","vertical"]),reversed:a.default.bool,disabled:a.default.bool},p={onChange:function(){return function(){}}(),loopDuration:15e3,maxFrames:100,orientation:"horizontal",reversed:!1,disabled:!1},d=function(e){function t(e){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t);var r=function(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}(this,(t.__proto__||Object.getPrototypeOf(t)).call(this,e));r.state={intervalId:null};var n=e.end-e.start,o=Math.min(e.maxFrames,n/e.step),a=n/o;return r.intervalMilliseconds=e.loopDuration/o,r.increment=a<e.step?e.step:a-a%e.step,r.onChange=r.onChange.bind(r),r.play=r.play.bind(r),r.pause=r.pause.bind(r),r.step=r.step.bind(r),r.getPlayClass=r.getPlayClass.bind(r),r.formatter=r.formatter.bind(r),r}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,o["default"].PureComponent),n(t,[{key:"componentDidMount",value:function(){return function(){u.default.bind(["space"],this.play)}}()},{key:"componentWillUnmount",value:function(){return function(){u.default.unbind(["space"])}}()},{key:"onChange",value:function(){return function(e){this.props.onChange(e.target.value),null!=this.state.intervalId&&this.pause()}}()},{key:"getPlayClass",value:function(){return function(){return null==this.state.intervalId?"fa fa-play fa-lg slider-button":"fa fa-pause fa-lg slider-button"}}()},{key:"play",value:function(){return function(){if(!this.props.disabled)if(null!=this.state.intervalId)this.pause();else{var e=setInterval(this.step,this.intervalMilliseconds);this.setState({intervalId:e})}}}()},{key:"pause",value:function(){return function(){clearInterval(this.state.intervalId),this.setState({intervalId:null})}}()},{key:"step",value:function(){return function(){var e=this;if(!this.props.disabled){var t=this.props.values.map(function(t){return t+e.increment});if(t[1]>this.props.end){var r=t[0]-this.props.start;t=t.map(function(e){return e-r})}this.props.onChange(t)}}}()},{key:"formatter",value:function(){return function(e){if(this.props.disabled)return(0,l.t)("Data has no time steps");var t=e;return Array.isArray(e)?e[0]===e[1]&&(t=[e[0]]):t=[e],t.map(function(e){return new Date(e).toUTCString()}).join(" : ")}}()},{key:"render",value:function(){return function(){return o.default.createElement(i.Row,{className:"play-slider"},o.default.createElement(i.Col,{md:1,className:"padded"},o.default.createElement("i",{className:this.getPlayClass(),onClick:this.play}),o.default.createElement("i",{className:"fa fa-step-forward fa-lg slider-button ",onClick:this.step})),o.default.createElement(i.Col,{md:11,className:"padded"},o.default.createElement(s.default,{value:this.props.values,formatter:this.formatter,change:this.onChange,min:this.props.start,max:this.props.end,step:this.props.step,orientation:this.props.orientation,reversed:this.props.reversed,disabled:this.props.disabled?"disabled":"enabled"})))}}()}]),t}();t.default=d,d.propTypes=f,d.defaultProps=p},2612:function(e,t,r){},2650:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var n=function(){return function(e,t){if(Array.isArray(e))return e;if(Symbol.iterator in Object(e))return function(e,t){var r=[],n=!0,o=!1,a=void 0;try{for(var i,u=e[Symbol.iterator]();!(n=(i=u.next()).done)&&(r.push(i.value),!t||r.length!==t);n=!0);}catch(e){o=!0,a=e}finally{try{!n&&u.return&&u.return()}finally{if(o)throw a}}return r}(e,t);throw new TypeError("Invalid attempt to destructure non-iterable instance")}}(),o=function(){function e(e,t){for(var r=0;r<t.length;r++){var n=t[r];n.enumerable=n.enumerable||!1,n.configurable=!0,"value"in n&&(n.writable=!0),Object.defineProperty(e,n.key,n)}}return function(t,r,n){return r&&e(t.prototype,r),n&&e(t,n),t}}(),a=u(r(1)),i=u(r(0));function u(e){return e&&e.__esModule?e:{default:e}}function s(e,t,r){return t in e?Object.defineProperty(e,t,{value:r,enumerable:!0,configurable:!0,writable:!0}):e[t]=r,e}r(2651);var l={categories:i.default.object,toggleCategory:i.default.func,showSingleCategory:i.default.func,position:i.default.oneOf(["tl","tr","bl","br"])},c={categories:{},toggleCategory:function(){return function(){}}(),showSingleCategory:function(){return function(){}}(),position:"tr"},f=function(e){function t(){return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t),function(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}(this,(t.__proto__||Object.getPrototypeOf(t)).apply(this,arguments))}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,a["default"].PureComponent),o(t,[{key:"render",value:function(){return function(){var e,t=this;if(0===Object.keys(this.props.categories).length)return null;var r=Object.entries(this.props.categories).map(function(e){var r=n(e,2),o=r[0],i=r[1],u={color:"rgba("+i.color.join(", ")+")"},s=i.enabled?"●":"○";return a.default.createElement("li",null,a.default.createElement("a",{href:"#",onClick:function(){return t.props.toggleCategory(o)},onDoubleClick:function(){return t.props.showSingleCategory(o)}},a.default.createElement("span",{style:u},s)," ",o))}),o="t"===this.props.position.charAt(0)?"top":"bottom",i="r"===this.props.position.charAt(1)?"right":"left",u=(s(e={},o,"0px"),s(e,i,"10px"),e);return a.default.createElement("div",{className:"legend",style:u},a.default.createElement("ul",{className:"categories"},r))}}()}]),t}();t.default=f,f.propTypes=l,f.defaultProps=c},2651:function(e,t,r){}}]);