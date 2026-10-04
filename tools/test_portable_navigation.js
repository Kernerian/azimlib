/* Development tests of the actual shipped DOM-independent JavaScript model. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {Navigation,inverse}=require('../src/azimlib/assets/navigation.js');
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),name=process.argv[3];
let checks=0;
function near(a,b){checks++;assert.ok(Math.abs(a-b)<=1e-8*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);}
function values(a,b){assert.equal(a.length,b.length);a.forEach((v,i)=>Array.isArray(v)?values(v,b[i]):near(v,b[i]));}
const n=new Navigation(fixture.maps);
const tests={
 reference(){
  for(const ref of fixture.reference.cases){
   const a=ref.action;
   if(a?.kind==='rectangle'){
    const [x,y,w,h]=n.viewport(a.index).box;n.rectangle(a.index,[x+w*.25,y+h*.25,w*.5,h*.5],{out:a.out});n.commit();
   }else if(a?.kind==='home')n.home();else if(a?.kind==='navigate')n.navigate(a.delta);
   values(n.views.map((_,i)=>n.extent(i)),ref.extents);values(n.views.map((_,i)=>n.viewport(i).box),ref.boxes);
   assert.equal(n.cursor,ref.cursor);assert.equal(n.history.length,ref.history);checks+=2;
  }
 },
 groups(){
  for(const c of fixture.cases){
   const nav=new Navigation(c.maps),before=nav.views.map((_,i)=>nav.extent(i));
   nav.setExtent(0,[-54,-46,-26,-18]);
   const x=nav.siblings(0,'x'),y=nav.siblings(0,'y');
   nav.views.forEach((_,i)=>{
    const e=nav.extent(i);values(e.slice(0,2),x.includes(i)?[-54,-46]:before[i].slice(0,2));
    values(e.slice(2),y.includes(i)?[-26,-18]:before[i].slice(2));
    const vp=nav.viewport(i),b=nav.views[i];near(vp.box[2]/vp.box[3],(b[2]-b[0])/(b[3]-b[1]));
   });
   nav.commit();nav.home();assert.ok(nav.views.every((b,i)=>b.every((v,j)=>v===nav.initial[i][j])));
  }
 },
 anchor(){
  const vp=n.viewport(0),[x,y,w,h]=vp.box,p={x:x+w*.3,y:y+h*.6};
  const before=[(p.x-vp.ox)/vp.scale,(vp.oy-p.y)/vp.scale];n.zoom(0,2,p);
  const after=n.viewport(0);values([(p.x-after.ox)/after.scale,(after.oy-p.y)/after.scale],before);
  const right=n.extent(1);values(right.slice(0,2),n.extent(0).slice(0,2));values(right.slice(2),[-20,0]);
  const old=n.extent(0);n.zoom(0,2,undefined,'x');values(n.extent(0).slice(2),old.slice(2));
  n.zoom(0,2,undefined,'y');values(n.extent(0).slice(0,2),n.extent(1).slice(0,2));
 },
 pan(){
  const before=n.extent(0),vp=n.viewport(0);n.pan(0,20,10);
  const e=n.extent(0),pr=fixture.maps[0].projection;
  const p=inverse(pr,n.initial[0][0]-20/vp.scale,n.initial[0][1]+10/vp.scale);
  near(e[0],p[0]);near(e[2],p[1]);near(e[1]-e[0],before[1]-before[0]);
  n.commit();const checkpoint=n.snapshot();n.pan(1,-15,0);n.commit();
  assert.ok(n.navigate(-1));values(n.snapshot(),checkpoint);assert.ok(n.navigate(1));
  n.navigate(-1);n.zoom(0,1.2);n.commit();assert.equal(n.navigate(1),false);
  const saved=n.snapshot(),length=n.history.length;n.pan(0,5,5);n.restoreViews(saved);
  assert.equal(n.commit(),false);assert.equal(n.history.length,length);values(n.snapshot(),saved);
 },
 mixed(){
  const nav=new Navigation(fixture.mixed);nav.setExtent(0,[-56,-42,-32,-16]);
  values(nav.extent(0),nav.extent(1));
  nav.zoom(1,2);values(nav.extent(0),nav.extent(1));
  nav.setExtent(0,[-30,30,-89,89]);values(nav.extent(0),nav.extent(1));
  assert.ok(nav.extent(0)[3]<=85.051128779807);assert.ok(nav.extent(0)[2]>=-85.051128779807);
 },
 dpi(){
  const a=new Navigation(fixture.maps),b=new Navigation(fixture.double);
  a.zoom(0,2);b.zoom(0,2);values(a.extent(0),b.extent(0));
  a.pan(0,20,10);b.pan(0,40,20);values(a.extent(0),b.extent(0));
  a.views.forEach((_,i)=>values(b.viewport(i).box,a.viewport(i).box.map(v=>v*2)));
 },
 invalid(){
  const saved=n.snapshot();
  for(const operation of [()=>n.zoom(0,0),()=>n.zoom(0,NaN),()=>n.pan(0,Infinity,0),()=>n.setExtent(0,[0,0,0,1]),()=>n.setExtent(0,[-200,0,-10,10]),()=>n.restoreViews([])]){
   assert.throws(operation);values(n.snapshot(),saved);checks++;
  }
  const unsupported=new Navigation(fixture.unsupported),initial=unsupported.snapshot();
  assert.throws(()=>unsupported.zoom(0,2),/cylindrical/);values(unsupported.snapshot(),initial);
  const unlinked=new Navigation(fixture.unsupported.map(m=>({...m,shared_axes:{x:[],y:[]}})));
  unlinked.zoom(1,2);assert.equal(unlinked.extent(1),null);assert.ok(unlinked.viewport(1).k>1);
  const external=new Navigation(fixture.maps.map(m=>({...m,shared_axes:{x:[m.axes_index,99],y:[]}})));
  external.zoom(0,2);values(external.extent(1),[-60,-40,-20,0]);
 },
 world(){
  n.setExtent(0,[-180,180,-80,80]);n.pan(0,1e8,1e8);const e=n.extent(0);
  assert.ok(e[0]>=-180-1e-8&&e[1]<=180+1e-8&&e[2]>=-90-1e-8&&e[3]<=90+1e-8);
  n.zoom(0,.000001);assert.ok(n.views[0].every(Number.isFinite));
  values(n.extent(1).slice(0,2),n.extent(0).slice(0,2));
 },
 nested(){
  const nav=new Navigation(fixture.nested);nav.zoom(2,2);
  nav.views.forEach((_,i)=>values(nav.extent(i),nav.extent(2)));
  nav.commit();nav.navigate(-1);assert.ok(nav.views.every((_,i)=>nav.isHome(i)));
  const sparse=new Navigation(fixture.sparse);sparse.zoom(0,2);
  sparse.views.forEach((_,i)=>values(sparse.extent(i),sparse.extent(0)));
 }
};
assert.ok(tests[name],name);tests[name]();console.log(JSON.stringify({test:name,checks}));
