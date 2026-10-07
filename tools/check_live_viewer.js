/* Original executable protocol/DOM fixture; not a browser or native input claim. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const sent=[],timers=[],frames=[];let observer,snapshot={revision:1,svg:'<svg width="400" height="200"></svg>',width:400,height:200,mode:'',back:false,forward:false};
const elements={};function element(id){return elements[id]??=( {style:{},textContent:'',innerHTML:'',disabled:false,dataset:{command:id},setAttribute(k,v){this[k]=v;},getBoundingClientRect(){return {left:10,top:20,width:402,height:202};},querySelector(){return {getAttribute(k){return k==='width'?'400':'200';}};},setPointerCapture(){this.capture=true;},hasPointerCapture(){return this.capture;},releasePointerCapture(){this.capture=false;},focus(){}});}
const buttons=['home','back','forward','pan','zoom'].map(element);const document={getElementById:element,querySelectorAll(selector){return selector.includes('pan]')?[element('pan'),element('zoom')]:buttons;},querySelector(selector){return buttons.find(b=>selector.includes(b.dataset.command));}};
const context={document,window:{addEventListener(){}},ResizeObserver:class{constructor(fn){observer=fn;}observe(){}},requestAnimationFrame(fn){frames.push(fn);return frames.length;},cancelAnimationFrame(){},setTimeout(fn){timers.push(fn);},fetch:async(url,options)=>{if(options){sent.push(JSON.parse(options.body));return {ok:true};}return {ok:true,json:async()=>snapshot};},Promise,Error,Number,Math,JSON};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/azimlib/assets/live-viewer.js'),'utf8'),context);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{await settle();const canvas=element('canvas');assert.match(canvas.innerHTML,/<svg/);
const pointer=(x,y,button=0,buttons=1)=>({clientX:x+10,clientY:y+20,button,buttons,pointerId:1});
canvas.onpointerdown(pointer(200,100));canvas.onpointermove(pointer(210,100));canvas.onpointermove(pointer(220,100));canvas.onpointerup(pointer(220,100));await settle();await settle();
assert.deepEqual(sent.map(r=>r.name),['button_press_event','motion_notify_event','button_release_event']);assert.equal(sent[1].x,220*400/402);assert.equal(sent[1].buttons[0],1);
sent.length=0;canvas.onpointerdown(pointer(100,100,2,2));canvas.onlostpointercapture();await settle();await settle();assert.deepEqual(sent.map(r=>r.button),[3,3]);
sent.length=0;observer();observer();await settle();assert.equal(sent.length,1);assert.equal(sent[0].op,'resize');
snapshot={...snapshot,coordinates:'x=1 y=2'};await timers.shift()();await settle();assert.equal(element('status').textContent,'x=1 y=2');
console.log(JSON.stringify({passed:true,input_order:true,motion_coalescing:true,lost_capture:true,resize_deduplicated:true,coordinates_without_repaint:true,scope:'Own DOM/protocol fixture; no real browser acceptance'}));})().catch(e=>{console.error(e);process.exitCode=1;});
