/* Actual shipped component model against our Python composition. */
const fs=require('node:fs'),assert=require('node:assert/strict');
const components=require('../src/azimlib/assets/components.js');
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let checks=0;
function near(a,b){checks++;assert.ok(Math.abs(a-b)<=1e-7*Math.max(1,Math.abs(a),Math.abs(b)),`${a} != ${b}`);}
for(const c of fixture.scales){
 let plan;
 if(c.error){assert.throws(()=>components.scale(c.component,c.meta,c.view));checks++;continue;}
 plan=components.scale(c.component,c.meta,c.view);
 assert.equal(plan.items.length,c.items.length);
 plan.items.forEach((p,i)=>{
  const q=c.items[i];assert.equal(p.kind,q.kind);assert.equal(p.fill,q.fill);assert.equal(p.stroke||'none',q.stroke||'none');
  for(const key of ['stroke_width','opacity','x','y','width','height','size'])if(key in q)near(p[key]??1,q[key]);
  if(p.kind==='text'){assert.equal(p.text,q.text);checks++;}
  if(p.points)p.points.forEach((point,j)=>point.forEach((v,k)=>near(v,q.points[j][k])));
 });
 const measured=plan.labels.map(([f,t])=>[f,components.width(t,c.component.metrics,c.component.options.fontsize*100/72*(c.meta.pixel_ratio||1))]);
 for(let i=1;i<measured.length;i++)assert.ok(measured[i-1][0]*plan.width+measured[i-1][1]/2<measured[i][0]*plan.width-measured[i][1]/2);
 if(plan.compact)assert.equal(plan.labels.length,1);
 assert.ok(Number.isFinite(plan.length)&&plan.length>0);checks++;
}
for(const c of fixture.orientations){components.orientationOffset(c.component,c.meta,c.view).forEach((v,i)=>near(v,c.offset[i]));}
for(const [number,expected] of fixture.formats){assert.equal(components.general(number),expected);checks++;}
console.log(JSON.stringify({checks,scales:fixture.scales.length,orientations:fixture.orientations.length}));
