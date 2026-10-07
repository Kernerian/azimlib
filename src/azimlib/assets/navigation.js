/* Own cartographic view model. No DOM, server, plotting or mapping framework. */
(function(root){'use strict';
const RAD=Math.PI/180,DEG=180/Math.PI;
const close=(a,b)=>Math.abs(a-b)<=1e-8*Math.max(1,Math.abs(a),Math.abs(b));
const equal=(a,b)=>a.length===b.length&&a.every((v,i)=>close(v,b[i]));
const cylindrical=pr=>['equirectangular','mercator'].includes(pr.name);
function project(pr,lon,lat){
 const R=pr.radius||6371008.8,lon0=pr.central_longitude||0,lat0=(pr.central_latitude||0)*RAD;
 const maximum=pr.max_latitude||85.0511287798066;
 if(pr.name==='mercator')lat=Math.max(-maximum,Math.min(maximum,lat));
 return [R*(lon-lon0)*RAD*(pr.name==='equirectangular'?Math.cos((pr.standard_parallel||0)*RAD):1),
  pr.name==='mercator'?R*(Math.log(Math.tan(Math.PI/4+lat*RAD/2))-Math.log(Math.tan(Math.PI/4+lat0/2))):R*(lat*RAD-lat0)];
}
function inverse(pr,x,y){
 if(!cylindrical(pr))return null;
 const R=pr.radius||6371008.8,lat0=(pr.central_latitude||0)*RAD;
 return [(pr.central_longitude||0)+x/R*DEG/(pr.name==='equirectangular'?Math.cos((pr.standard_parallel||0)*RAD):1),
  pr.name==='mercator'?(2*Math.atan(Math.exp(y/R+Math.log(Math.tan(Math.PI/4+lat0/2))))-Math.PI/2)*DEG:(y/R+lat0)*DEG];
}
function extentBounds(pr,extent){
 const [w,e,s,n]=extent,a=project(pr,w,s),b=project(pr,e,n);
 return [a[0],a[1],b[0],b[1]];
}
function interval(lo,hi,minimum,maximum){
 const span=Math.min(maximum-minimum,Math.max(1e-6,hi-lo));
 const left=Math.max(minimum,Math.min(maximum-span,lo));return [left,left+span];
}
function valid(bounds){return bounds.length===4&&bounds.every(Number.isFinite)&&bounds[0]<bounds[2]&&bounds[1]<bounds[3];}

class Navigation {
 constructor(metadata){
  this.metadata=metadata;this.initial=metadata.map(m=>m.projected_bounds.slice());
  this.views=this.initial.map(b=>b.slice());this.history=[this.snapshot()];this.cursor=0;
 }
 snapshot(){return this.views.map(b=>b.slice());}
 restoreViews(views){
  if(views.length!==this.views.length||views.some(b=>!valid(b)))throw new Error('Invalid view snapshot');
  this.views=views.map(b=>b.slice());
 }
 isHome(i){return equal(this.views[i],this.initial[i]);}
 portable(i){
  const m=this.metadata[i];if(m.bearing||!cylindrical(m.projection))return false;
  const [w,s,e,n]=m.extent;
  return equal(extentBounds(m.projection,[w,e,s,n]),m.projected_bounds);
 }
 viewport(i){
  const m=this.metadata[i],bounds=this.views[i];
  if(this.isHome(i))return {box:m.box.slice(),scale:m.scale,ox:m.ox,oy:m.oy,k:1,tx:0,ty:0,bounds:bounds.slice()};
  const [x,y,w,h]=m.navigation_box||m.box,[x0,y0,x1,y1]=bounds;
  const scale=Math.min(w/(x1-x0),h/(y1-y0)),width=(x1-x0)*scale,height=(y1-y0)*scale;
  const box=[x+(w-width)/2,y+(h-height)/2,width,height],ox=box[0]-x0*scale,oy=box[1]+y1*scale;
  const k=scale/m.scale;
  return {box,scale,ox,oy,k,tx:ox-m.ox*k,ty:oy-m.oy*k,bounds:bounds.slice()};
 }
 extent(i){
  if(!this.portable(i))return null;
  const pr=this.metadata[i].projection,b=this.views[i],a=inverse(pr,b[0],b[1]),c=inverse(pr,b[2],b[3]);
  return [a[0],c[0],a[1],c[1]];
 }
 siblings(i,name){
  const members=this.metadata[i].shared_axes?.[name]||[];
  return this.metadata.map((m,j)=>j).filter(j=>j===i||members.includes(this.metadata[j].axes_index));
 }
 normalize(i,bounds){
  if(!valid(bounds))throw new Error('Invalid geographic view');
  if(!this.portable(i))return bounds.slice();
  const pr=this.metadata[i].projection,limit=pr.name==='mercator'?(pr.max_latitude||85.0511287798066):90;
  const lon0=pr.central_longitude||0;
  const world=extentBounds(pr,[this.metadata[i].longitude_wrap?lon0-180:Math.max(-180,lon0-180),this.metadata[i].longitude_wrap?lon0+180:Math.min(180,lon0+180),-limit,limit]);
  const x=interval(bounds[0],bounds[2],world[0],world[2]),y=interval(bounds[1],bounds[3],world[1],world[3]);
  return [x[0],y[0],x[1],y[1]];
 }
 update(i,bounds){
  const links={x:this.siblings(i,'x'),y:this.siblings(i,'y')},linked=[...new Set([...links.x,...links.y])];
  if(linked.length>1&&linked.some(j=>!this.portable(j)))throw new Error('Linked navigation requires cylindrical views. Use the Python/Tk viewer for these projections.');
  const next=this.snapshot();next[i]=this.normalize(i,bounds);
  if(linked.length>1){
   if(links.y.length>1){
    const maximum=Math.min(...links.y.map(j=>this.metadata[j].projection.name==='mercator'?(this.metadata[j].projection.max_latitude||85.0511287798066):90));
    const pr=this.metadata[i].projection,a=inverse(pr,next[i][0],next[i][1]),b=inverse(pr,next[i][2],next[i][3]);
    const [south,north]=interval(a[1],b[1],-maximum,maximum);
    next[i][1]=project(pr,0,south)[1];next[i][3]=project(pr,0,north)[1];
   }
   if(links.x.length>1){
    const minimum=Math.max(...links.x.map(j=>this.metadata[j].longitude_wrap?(this.metadata[j].projection.central_longitude||0)-180:Math.max(-180,(this.metadata[j].projection.central_longitude||0)-180)));
    const maximum=Math.min(...links.x.map(j=>this.metadata[j].longitude_wrap?(this.metadata[j].projection.central_longitude||0)+180:Math.min(180,(this.metadata[j].projection.central_longitude||0)+180)));
    const pr=this.metadata[i].projection,a=inverse(pr,next[i][0],next[i][1]),b=inverse(pr,next[i][2],next[i][3]);
    const [west,east]=interval(a[0],b[0],minimum,maximum);
    next[i][0]=project(pr,west,0)[0];next[i][2]=project(pr,east,0)[0];
   }
   const pr=this.metadata[i].projection,a=inverse(pr,next[i][0],next[i][1]),b=inverse(pr,next[i][2],next[i][3]);
   for(const name of ['x','y'])for(const j of links[name]){
    if(j===i)continue;
    const target=this.metadata[j].projection;
    if(name==='x'){next[j][0]=project(target,a[0],0)[0];next[j][2]=project(target,b[0],0)[0];}
    else{next[j][1]=project(target,0,a[1])[1];next[j][3]=project(target,0,b[1])[1];}
    next[j]=this.normalize(j,next[j]);
   }
  }
  // Validate/prepare all members before committing any of them.
  if(next.some(b=>!valid(b)))throw new Error('Invalid linked view');
  const changed=next.map((b,j)=>j).filter(j=>!equal(next[j],this.views[j]));this.views=next;return changed;
 }
 setExtent(i,extent){
  if(!this.portable(i))throw new Error('Geographic bounds require a cylindrical view');
  extent=extent.slice();const wrapped=this.metadata[i].longitude_wrap,c=wrapped?(this.metadata[i].projection.central_longitude||0):0;
  if(wrapped&&extent[0]>extent[1])extent[1]+=360;
  if(wrapped){const shift=360*Math.round((c-(extent[0]+extent[1])/2)/360);extent[0]+=shift;extent[1]+=shift;}
  if(extent.length!==4||!extent.every(Number.isFinite)||extent[0]>=extent[1]||extent[2]>=extent[3]||extent[0]<c-180||extent[1]>c+180||extent[2]<-90||extent[3]>90)throw new Error('Invalid geographic extent');
  return this.update(i,extentBounds(this.metadata[i].projection,extent));
 }
 zoom(i,factor,point,constraint=''){
  if(!Number.isFinite(factor)||factor<=0)throw new Error('Zoom factor must be positive');
  const vp=this.viewport(i),[x,y,w,h]=vp.box,p=point||{x:x+w/2,y:y+h/2};
  const cx=(p.x-vp.ox)/vp.scale,cy=(vp.oy-p.y)/vp.scale,b=this.views[i];
  const k=Math.max(.05,Math.min(10000,vp.k*factor)),ratio=k/vp.k;
  return this.update(i,[constraint==='y'?b[0]:cx+(b[0]-cx)/ratio,constraint==='x'?b[1]:cy+(b[1]-cy)/ratio,
   constraint==='y'?b[2]:cx+(b[2]-cx)/ratio,constraint==='x'?b[3]:cy+(b[3]-cy)/ratio]);
 }
 pan(i,dx,dy,constraint=''){
  if(!Number.isFinite(dx+dy))throw new Error('Pan offsets must be finite');
  const vp=this.viewport(i),b=this.views[i],x=constraint==='y'?0:-dx/vp.scale,y=constraint==='x'?0:dy/vp.scale;
  return this.update(i,[b[0]+x,b[1]+y,b[2]+x,b[3]+y]);
 }
 rectangle(i,rect,{out=false,constraint=''}={}){
  const vp=this.viewport(i),[x,y,w,h]=vp.box,[rx,ry,rw,rh]=rect;
  if(!rect.every(Number.isFinite)||rw<5||rh<5)return [];
  const left=Math.max(x,Math.min(x+w,rx)),right=Math.max(x,Math.min(x+w,rx+rw));
  const top=Math.max(y,Math.min(y+h,ry)),bottom=Math.max(y,Math.min(y+h,ry+rh));
  if(right-left<5||bottom-top<5)return [];
  const old=this.views[i],b=[constraint==='y'?old[0]:(left-vp.ox)/vp.scale,constraint==='x'?old[1]:(vp.oy-bottom)/vp.scale,
   constraint==='y'?old[2]:(right-vp.ox)/vp.scale,constraint==='x'?old[3]:(vp.oy-top)/vp.scale];
  if(out)for(const [a,c] of [[0,2],[1,3]]){
   const f=(old[c]-old[a])/(b[c]-b[a]),low=old[a]-f*(b[a]-old[a]),high=old[c]+f*(old[c]-b[c]);b[a]=low;b[c]=high;
  }
  return this.update(i,b);
 }
 center(i,point){
  if(!Array.isArray(point)||point.length!==2||!point.every(Number.isFinite))throw new Error('Invalid projected center');
  const b=this.views[i],w=(b[2]-b[0])/2,h=(b[3]-b[1])/2;
  return this.update(i,[point[0]-w,point[1]-h,point[0]+w,point[1]+h]);
 }
 commit(){
  const current=this.snapshot(),previous=this.history[this.cursor];
  if(current.every((b,i)=>equal(b,previous[i])))return false;
  this.history=this.history.slice(0,this.cursor+1);this.history.push(current);this.cursor++;return true;
 }
 home(){this.restoreViews(this.initial);this.commit();}
 navigate(delta){
  const next=this.cursor+delta;if(next<0||next>=this.history.length)return false;
  this.cursor=next;this.restoreViews(this.history[next]);return true;
 }
}
const api={Navigation,project,inverse,extentBounds};
if(typeof module==='object'&&module.exports)module.exports=api;else root.AzimlibNavigation=api;
})(typeof globalThis==='object'?globalThis:this);
