/* Azimlib's own SVG navigation; no mapping or plotting framework. */
(()=>{'use strict';
const NS='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id);
const canvas=$('canvas'),svg=canvas.querySelector(':scope > svg'),mini=$('mini');
const metadata=JSON.parse($('map-data').textContent);
const navigation=new AzimlibNavigation.Navigation(metadata);
const original=[...svg.children].filter(el=>!['defs'].includes(el.localName));
// The renderer emits exactly one root node per scene primitive, plus background.
const nodes=original.slice(1); // Figure always has a background in the viewer.
const make=(tag,attrs={})=>{const el=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));return el;};
let active=0,mode='',drag=null,wheelTimer=null,axisConstraint='',lastError='';
const states=metadata.map((m,index)=>{
 const [x,y,w,h]=m.box, wrap=make('g',{'data-map':index}),inner=make('g',{'data-map-content':index});
 const defs=make('defs'),clip=make('clipPath',{id:`view-clip-${index}`});clip.append(make('rect',{x,y,width:w,height:h}));defs.append(clip);wrap.append(defs);
 const clipped=make('g',{'clip-path':`url(#view-clip-${index})`});clipped.append(inner);wrap.append(clipped);
 const staticSet=new Set([...(m.static_indices||[]),...(m.tick_indices||[])]);
 const movable=nodes.slice(m.start,m.end).filter((_,i)=>!staticSet.has(i+m.start));
 if(movable.length)svg.insertBefore(wrap,movable[0]);else svg.append(wrap);
 for(const el of movable){
  el.removeAttribute('clip-path');el.querySelectorAll('[clip-path]').forEach(n=>n.removeAttribute('clip-path'));
  [el,...el.querySelectorAll('path,rect,circle')].forEach(n=>{if(n.localName!=='g')n.setAttribute('vector-effect','non-scaling-stroke');});
  inner.append(el);
 }
 const ticks=(m.tick_indices||[]).map(i=>nodes[i]).filter(Boolean);
 const dynamic=make('g',{'data-dynamic-ticks':index});svg.append(dynamic);
 dynamic.style.display=m.ticks?'':'none';
 const textNodes=[...inner.querySelectorAll('text')].map(n=>[n,Number(n.getAttribute('font-size'))||12]);
 const circles=[...inner.querySelectorAll('circle')].map(n=>[n,Number(n.getAttribute('r'))]);
 const decorations=nodes.slice(m.decoration_start,m.decoration_end);
 const dynamicComponents=make('g',{'data-dynamic-components':index});
 if((m.components||[]).length)svg.insertBefore(dynamicComponents,decorations.at(-1)?.nextSibling||null);
 const gridNodes=(m.grid_indices||[]).map(i=>nodes[i]);
 const dynamicGrid=make('g',{'data-dynamic-grid':index});
 if(gridNodes.length)inner.insertBefore(dynamicGrid,gridNodes[0]);
 else inner.append(dynamicGrid);
 const anchorTransforms=new Map((m.anchor_ranges||[]).flatMap(a=>a.indices.map(i=>[i,nodes[i]?.getAttribute('transform')||''])));
 return {index,meta:m,inner,wrap,clip:clip.firstElementChild,ticks,dynamic,textNodes,circles,decorations,dynamicComponents,componentErrors:[],gridNodes,dynamicGrid,anchorTransforms,gridVisible:true,k:1,tx:0,ty:0};
});
states.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Axes ${i+1}`;$('axes-select').append(o);});
if(states.length<2)$('axes-select').hidden=true;
if(!states.length){$('overview').hidden=true;document.querySelectorAll('.toolbar button').forEach(b=>b.disabled=true);return;}
function state(){return states[active];}
function snapshot(s){const v=navigation.viewport(s.index);return {k:v.k,tx:v.tx,ty:v.ty};}
function commit(){navigation.commit();buttons();}
function flushWheel(){if(wheelTimer){clearTimeout(wheelTimer);wheelTimer=null;commit();}}
function buttons(){$('back').disabled=navigation.cursor===0;$('forward').disabled=navigation.cursor===navigation.history.length-1;}
function rect(node,box){if(node)['x','y','width','height'].forEach((key,i)=>node.setAttribute(key,box[i]));}
function draw(s){
 const vp=navigation.viewport(s.index),home=navigation.isHome(s.index);s.view=vp;Object.assign(s,snapshot(s));
 s.inner.setAttribute('transform',`translate(${s.tx} ${s.ty}) scale(${s.k})`);
 rect(s.clip,vp.box);rect(nodes[s.meta.background_index],vp.box);
 const[x,y,w,h]=vp.box,[ox,oy,ow,oh]=s.meta.box,edges={left:`M${x},${y}V${y+h}`,right:`M${x+w},${y}V${y+h}`,top:`M${x},${y}H${x+w}`,bottom:`M${x},${y+h}H${x+w}`};
 Object.entries(s.meta.frame_indices||{}).forEach(([side,i])=>{const node=nodes[i];if(node)(node.querySelector('path')||node).setAttribute('d',edges[side]);});
 for(const a of s.meta.anchor_ranges||[]){
  const fraction=a.kind==='ylabel'?0:a.kind==='title'?({left:0,right:1}[a.align]??.5):.5;
  const dx=x-ox+(w-ow)*fraction,dy=y-oy+(h-oh)*(a.kind==='xlabel'?1:a.kind==='ylabel'?.5:0);
  a.indices.forEach(i=>{const n=nodes[i];if(n)n.setAttribute('transform',`translate(${dx} ${dy}) ${s.anchorTransforms.get(i)||''}`);});
 }
 s.textNodes.forEach(([n,f])=>n.setAttribute('font-size',f/s.k));s.circles.forEach(([n,r])=>n.setAttribute('r',r/s.k));
 s.ticks.forEach(n=>n.style.display=home?'':'none');s.decorations.forEach(n=>n.style.display=home?'':'none');dynamicTicks(s);dynamicDecorations(s,home);
}
function dynamicDecorations(s,home){
 s.dynamicComponents.replaceChildren();s.componentErrors=[];
 if(home)return;
 if(!navigation.portable(s.index))return;
 for(const component of s.meta.components||[]){
  const group=make('g',{'data-component':component.kind});
  if(component.kind==='scale'){
   let plan;
   try{plan=AzimlibComponents.scale(component,s.meta,s.view);}
   catch(error){s.componentErrors.push(error.message);continue;}
   group.setAttribute('data-length',plan.length);group.setAttribute('data-units',plan.units);
   for(const p of plan.items){
    const common={fill:p.fill,stroke:p.stroke||'none','stroke-width':p.stroke_width||0,'stroke-linejoin':'round',opacity:p.opacity??1};
    if(p.kind==='path')group.append(make('path',{...common,d:'M'+p.points.map(v=>v.join(',')).join('L')+'Z'}));
    else if(p.kind==='rect')group.append(make('rect',{...common,x:p.x,y:p.y,width:p.width,height:p.height}));
    else{const text=make('text',{...common,x:p.x,y:p.y,'font-family':'DejaVu Sans','font-size':p.size,'text-anchor':'middle','dominant-baseline':'alphabetic'});text.textContent=p.text;group.append(text);}
   }
  }else{
   const [dx,dy]=AzimlibComponents.orientationOffset(component,s.meta,s.view);
   group.setAttribute('transform',`translate(${dx} ${dy})`);
   for(const i of component.indices){const clone=nodes[i]?.cloneNode(true);if(clone){clone.style.display='';group.append(clone);}}
  }
  s.dynamicComponents.append(group);
 }
}
function redraw(){states.forEach(draw);overview();buttons();}
function attempt(action,{push=false}={}){
 try{action();lastError='';redraw();if(push)commit();const warnings=states.flatMap(s=>s.componentErrors);if(warnings.length)$('coordinates').textContent='Scale: '+warnings[0];return true;}
 catch(error){lastError=error.message;$('coordinates').textContent=lastError;return false;}
}
function select(index){active=index;$('axes-select').value=index;overview();buttons();$('overview').hidden=true;}
function locator(s){
 const m=s.meta.overview_map;if(!m)return;
 const [x,y,w,h]=m.box,[ax,ay,aw,ah]=s.view.box;
 const transform=(sx,sy)=>{
  const px=((sx-s.tx)/s.k-s.meta.ox)/s.meta.scale;
  const py=(s.meta.oy-(sy-s.ty)/s.k)/s.meta.scale;
  return [m.ox+px*m.scale,m.oy-py*m.scale];
 };
 const a=transform(ax,ay),b=transform(ax+aw,ay+ah);
 const x0=Math.max(x,Math.min(x+w,Math.min(a[0],b[0]))),x1=Math.max(x,Math.min(x+w,Math.max(a[0],b[0])));
 const y0=Math.max(y,Math.min(y+h,Math.min(a[1],b[1]))),y1=Math.max(y,Math.min(y+h,Math.max(a[1],b[1])));
 const boxes=[[x,y,w,y0-y],[x,y1,w,y+h-y1],[x,y0,x0-x,y1-y0],[x1,y0,x+w-x1,y1-y0],[x0,y0,x1-x0,y1-y0]];
 [...m.shade_indices,m.focus_index].forEach((index,i)=>['x','y','width','height'].forEach((key,j)=>nodes[index].setAttribute(key,boxes[i][j])));
}
function overview(){states.forEach(locator);$('zoom-level').textContent=`${state().k.toFixed(2)}×`;}
// The same locator belongs to the exported SVG; no duplicate floating widget.
svg.addEventListener('pointerdown',e=>{
 const p=position(e);
 for(let i=0;i<states.length;i++){
  const s=states[i],m=s.meta.overview_map;if(!m)continue;
  const [x,y,w,h]=m.box;if(p.x<x||p.x>x+w||p.y<y||p.y>y+h)continue;
  e.preventDefault();e.stopImmediatePropagation();select(i);
  const px=(p.x-m.ox)/m.scale,py=(m.oy-p.y)/m.scale;
  flushWheel();attempt(()=>navigation.center(i,[px,py]),{push:true});break;
 }
},true);
function position(event,element=svg){const p=new DOMPoint(event.clientX,event.clientY);return p.matrixTransform(element.getScreenCTM().inverse());}
function findMap(p){for(let i=states.length-1;i>=0;i--){const[x,y,w,h]=navigation.viewport(i).box;if(p.x>=x&&p.x<=x+w&&p.y>=y&&p.y<=y+h)return i;}return -1;}
function zoomCenter(factor){flushWheel();attempt(()=>navigation.zoom(active,factor,undefined,axisConstraint),{push:true});}
function setMode(value){flushWheel();cancelDrag();mode=mode===value?'':value;canvas.classList.toggle('pan',mode==='pan');canvas.classList.toggle('zoom',mode==='zoom');$('pan').setAttribute('aria-pressed',String(mode==='pan'));$('zoom').setAttribute('aria-pressed',String(mode==='zoom'));}
function restore(){flushWheel();cancelDrag();attempt(()=>navigation.home());}
function navigate(delta){flushWheel();cancelDrag();attempt(()=>navigation.navigate(delta));}
function coordinate(s,p){const m=s.meta,pr=m.projection, R=pr.radius||6371008.8;
 const xx=((p.x-s.tx)/s.k-m.ox)/m.scale,yy=(m.oy-(p.y-s.ty)/s.k)/m.scale;
 if(['equirectangular','mercator'].includes(pr.name)){
  const result=AzimlibNavigation.inverse(pr,xx,yy);
  return result.every(Number.isFinite)&&result[0]>=(m.longitude_wrap?(pr.central_longitude||0)-180:-180)-.000001&&result[0]<=(m.longitude_wrap?(pr.central_longitude||0)+180:180)+.000001&&Math.abs(result[1])<=90.000001?result:null;
 }
 const rad=Math.PI/180,deg=180/Math.PI,lon0=pr.central_longitude||0,lat0=(pr.central_latitude||0)*rad;
 let lon,lat;
 if(pr.name==='equirectangular'){lon=lon0+xx/R/Math.cos((pr.standard_parallel||0)*rad)*deg;lat=(yy/R+lat0)*deg;}
 else if(pr.name==='mercator'){lon=lon0+xx/R*deg;lat=(2*Math.atan(Math.exp(yy/R+Math.log(Math.tan(Math.PI/4+lat0/2))))-Math.PI/2)*deg;}
 else if(['stereographic','azimuthal_equidistant'].includes(pr.name)){const rho=Math.hypot(xx,yy)/R;if(rho<1e-12)return[lon0,lat0*deg];const c=pr.name==='stereographic'?2*Math.atan(rho/2):rho;if(c>=Math.PI-1e-14)return null;lat=Math.asin(Math.max(-1,Math.min(1,Math.cos(c)*Math.sin(lat0)+yy/R*Math.sin(c)*Math.cos(lat0)/rho)))*deg;lon=lon0+Math.atan2(xx/R*Math.sin(c),rho*Math.cos(lat0)*Math.cos(c)-yy/R*Math.sin(lat0)*Math.sin(c))*deg;}
 else if(pr.name==='orthographic'){const rho=Math.hypot(xx,yy)/R;if(rho>1)return null;if(rho<1e-12)return[lon0,lat0*deg];const c=Math.asin(rho);lat=Math.asin(Math.cos(c)*Math.sin(lat0)+yy/R*Math.sin(c)*Math.cos(lat0)/rho)*deg;lon=lon0+Math.atan2(xx/R*Math.sin(c),rho*Math.cos(lat0)*Math.cos(c)-yy/R*Math.sin(lat0)*Math.sin(c))*deg;}
 else if(pr.name==='equalearth'){let theta=yy/R/1.340264;for(let i=0;i<12;i++){const t2=theta*theta,poly=theta*(1.340264-.081106*t2+t2**3*(.000893+.003796*t2)),der=1.340264+3*(-.081106)*t2+7*.000893*t2**3+9*.003796*t2**4;theta-=(poly-yy/R)/der;}const t2=theta*theta,der=1.340264-3*.081106*t2+7*.000893*t2**3+9*.003796*t2**4;lat=Math.asin(2/Math.sqrt(3)*Math.sin(theta))*deg;lon=lon0+xx/R*3*der/(2*Math.sqrt(3)*Math.cos(theta))*deg;}
 else return {x:xx,y:yy};
 if(!Number.isFinite(lon+lat)||Math.abs(lat)>90||Math.abs(lon-lon0)>180.0001)return null;return[((lon+180)%360+360)%360-180,lat];}
function showCoordinate(s,p){const c=coordinate(s,p);$('coordinates').textContent=!c?'':Array.isArray(c)?`x=${c[0].toFixed(2)}  y=${c[1].toFixed(2)}`:`x=${c.x.toFixed(0)} m  y=${c.y.toFixed(0)} m`;}
function portableLabel(formatter,value,index,step){
 if(formatter.kind==='null')return '';
 if(formatter.kind==='fixed')return formatter.labels[index]||'';
 if(formatter.kind==='scalar'){
  const v=Math.abs(value)<step*1e-8?0:value;
  const digits=Math.max(0,Math.min(20,-Math.floor(Math.log10(step))+((step/10**Math.floor(Math.log10(step)))%1?1:0)));
  const text=v.toFixed(digits);return formatter.unicode_minus===false?text:text.replace('-','−');
 }
 if(formatter.kind==='longitude'&&Math.abs(value)>180){const original=value;value=((value+180)%360+360)%360-180;if(value===-180&&original>0)value=180;}
 const f=formatter,negative=value<0||Object.is(value,-0),absolute=Math.abs(value);
 let suffix=f.kind==='longitude'?(negative?'W':'E'):(negative?'S':'N');
 if(!value&&!f.zero_direction_label||f.kind==='longitude'&&absolute===180&&!f.dateline_direction_label)suffix='';
 const number=f.direction_label?absolute:value;let text;
 if(f.dms){const total=Math.round(absolute*3600000)/1000,degree=Math.floor(total/3600),minute=Math.floor((total-degree*3600)/60),second=+(total-degree*3600-minute*60).toFixed(3);
  text=`${degree}${f.degree_symbol}`;if(minute||second)text+=`${minute}′`;if(second)text+=`${second}″`;if(number<0)text='−'+text;
 }else{const match=/^\.(\d+)([feg])$/.exec(f.number_format),digits=match?+match[1]:6;
  text=match&&match[2]==='f'?number.toFixed(digits):match&&match[2]==='e'?number.toExponential(digits):String(+number.toPrecision(Math.max(1,digits)));
  text=text.replace('-','−')+f.degree_symbol;
 }
 return text+(f.direction_label?suffix:'');
}
function dynamicTicks(s){
 s.dynamic.replaceChildren();s.dynamicGrid.replaceChildren();
 const home=navigation.isHome(s.index),pr=s.meta.projection;
 const cylindrical=['equirectangular','mercator'].includes(pr.name);
 s.gridNodes.forEach(n=>n.style.display=s.gridVisible&&(home||!cylindrical&&!s.meta.custom_ticks)?'':'none');
 if(home||!cylindrical||s.meta.custom_ticks&&!s.meta.portable_ticks)return;
 const[x,y,w,h]=s.view.box,a=coordinate(s,{x,y:y+h}),b=coordinate(s,{x:x+w,y});
 if(!Array.isArray(a)||!Array.isArray(b))return;
 const rad=Math.PI/180,R=pr.radius||6371008.8,lon0=pr.central_longitude||0,lat0=(pr.central_latitude||0)*rad,ratio=s.meta.pixel_ratio||1,POINT=100/72*ratio;
 function projected(v,axis){
  if(axis==='x'){const mx=(v-lon0)*rad*R*(pr.name==='equirectangular'?Math.cos((pr.standard_parallel||0)*rad):1);return s.k*(s.meta.ox+mx*s.meta.scale)+s.tx;}
  const my=pr.name==='mercator'?R*(Math.log(Math.tan(Math.PI/4+v*rad/2))-Math.log(Math.tan(Math.PI/4+lat0/2))):R*(v*rad-lat0);
  return s.k*(s.meta.oy-my*s.meta.scale)+s.ty;
 }
 function range(lo,hi,step,origin=0,rounding=false){
  if(!Number.isFinite(step)||step<=0)return [];
  const first=rounding?Math.round((lo-origin)/step):Math.floor((lo-origin)/step),last=rounding?Math.round((hi-origin)/step):Math.ceil((hi-origin)/step);
  if(last-first>1500)return [];return Array.from({length:Math.max(0,last-first+1)},(_,i)=>origin+(first+i)*step);
 }
 const axes={};
 for(const[axis,lo,hi]of[['x',a[0],b[0]],['y',a[1],b[1]]]){
  const config=s.meta.portable_ticks?.[axis],loc=config?.locator;
  let bins=Math.max(2,Math.min(9,(axis==='x'?w:h)/ratio/(axis==='x'?65:42)));
  if((s.meta.shared_axes?.[axis]||[]).length>1){
   const owner=states.find(t=>t.meta.axes_index===s.meta.shared_tick_owner?.[axis])||s;
   const bounds=navigation.views[owner.index],[tw,th]=owner.meta.tick_area||owner.meta.navigation_box?.slice(2)||owner.meta.box.slice(2);
   const scale=Math.min(tw/(bounds[2]-bounds[0]),th/(bounds[3]-bounds[1]));
   bins=Math.max(2,Math.min(9,Math.floor((axis==='x'?(bounds[2]-bounds[0]):(bounds[3]-bounds[1]))*scale/ratio/(axis==='x'?65:42))));
  }
  let target=(hi-lo)/bins,pow=10**Math.floor(Math.log10(target));
  let step=[1,2,2.5,5,10].map(v=>v*pow).find(v=>v>=target)||pow*10;
  if(s.meta.grid_format?.labels&&!s.meta.major_locator_explicit?.[axis]&&(s.meta.shared_axes?.[axis]||[]).length<2)step=s.meta.grid_format.step||[1,2,5,10,15,20,30,45,60,90].find(v=>v>=Math.max(b[0]-a[0],b[1]-a[1])/6)||90;
  if(loc?.kind==='multiple')step=loc.base;
  const major=loc?.kind==='fixed'?loc.values:range(lo,hi,step,loc?.offset||0);
  const minorConfig=s.meta.portable_minor_ticks?.[axis],minorLoc=minorConfig?.locator;
  let minor=[];
  if(minorLoc?.kind==='fixed')minor=minorLoc.values;
  else if(minorLoc?.kind==='multiple')minor=range(lo,hi,minorLoc.base,minorLoc.offset||0);
  else if(minorLoc?.kind==='auto_minor'){
   const unique=[...new Set(major)].sort((a,b)=>a-b);
   if(unique.length>=2){const interval=unique[1]-unique[0],mantissa=interval/10**Math.floor(Math.log10(interval));
    const n=minorLoc.ndivs==='auto'?([1,2.5,5,10].some(v=>Math.abs(v-mantissa)<=v*1e-5)?5:4):minorLoc.ndivs;
    minor=range(lo,hi,interval/n,unique[0],true);
   }
  }
  const tolerance=(hi-lo)*1e-5;
  if(s.meta.minor_remove_overlap?.[axis]!==false)minor=minor.filter(v=>!major.some(m=>Math.abs(v-m)<=tolerance));
  axes[axis]={lo,hi,step,major,minor,config,minorConfig};
 }
 // Separate grid generation preserves per-axis/per-group style and step.
 if(s.gridVisible)for(const spec of s.meta.grid_specs||[]){
  const q=axes[spec.axis];let values=spec.step==null?q[spec.which]:range(q.lo,q.hi,spec.step);
  if(spec.which==='minor')values=values.filter(v=>!q.major.some(m=>Math.abs(v-m)<1e-8));
  const paint=spec.style,template=nodes[spec.indices[0]]||make('path',{fill:'none',stroke:paint.stroke,'stroke-width':paint.stroke_width*ratio,'stroke-dasharray':paint.dash.map(v=>v*ratio).join(' '),'stroke-linecap':paint.linecap,opacity:paint.opacity,'vector-effect':'non-scaling-stroke'});
  for(const v of values){if(v<q.lo-1e-8||v>q.hi+1e-8)continue;
   const grid=template.cloneNode(false),p=projected(v,spec.axis);grid.removeAttribute('style');
   const d=spec.axis==='x'?`M${(p-s.tx)/s.k},${(y-s.ty)/s.k}V${(y+h-s.ty)/s.k}`:`M${(x-s.tx)/s.k},${(p-s.ty)/s.k}H${(x+w-s.tx)/s.k}`;
   grid.setAttribute('d',d);s.dynamicGrid.append(grid);
  }
 }
 const defaults={direction:'out',length:3.5,width:.8,color:'black',labelcolor:'black',labelsize:10,pad:3.5,rotation:0,bottom:true,left:true,labelbottom:true,labelleft:true};
 for(const[axis,q]of Object.entries(axes))for(const which of ['major','minor']){
  const settings={...defaults,...s.meta.tick_settings?.[which]?.[axis]},config=which==='minor'?q.minorConfig:q.config,values=q[which];
  values.forEach((v,index)=>{if(v<q.lo-1e-8||v>q.hi+1e-8)return;
   const p=projected(v,axis),length=settings.length*POINT,inward=settings.direction==='in'?length:settings.direction==='inout'?length/2:0,outward=length-inward;
   const sourceIndex=config?.locator.kind==='fixed'?config.locator.values.indexOf(v):index;
   const label=which==='minor'&&!config?'':portableLabel(config?.formatter||{kind:s.meta.degree_ticks?(axis==='x'?'longitude':'latitude'):'scalar',direction_label:true,degree_symbol:'°',number_format:'g'},v,sourceIndex,q.step);
   for(const side of axis==='x'?['bottom','top']:['left','right']){
    const horizontal=axis==='x',sign=side==='bottom'||side==='right'?1:-1,base=horizontal?(side==='bottom'?y+h:y):(side==='left'?x:x+w);
    const offset=base+sign*(outward+settings.pad*POINT),tx=horizontal?p:offset,ty=horizontal?offset:p;
    if(settings[side]&&length>0&&settings.width>0)s.dynamic.append(make('path',{d:horizontal?`M${p},${base-sign*inward}V${base+sign*outward}`:`M${base-sign*inward},${p}H${base+sign*outward}`,stroke:settings.color,'stroke-width':settings.width*POINT}));
    if(!settings['label'+side]||!label)continue;
    const anchor=horizontal?'middle':sign<0?'end':'start',baseline=horizontal?(sign>0?'top':'bottom'):'middle';
    const plan=AzimlibComponents.textPlan(label,config?.metrics||s.meta.tick_metrics?.[axis],settings.labelsize*POINT,anchor,baseline,settings.rotation,settings.rotation_mode||'default');
    for(const row of plan.rows){
     const xx=tx+row.x,yy=ty+row.y;
     const t=make('text',{x:xx,y:yy,'font-family':'DejaVu Sans, sans-serif','font-size':settings.labelsize*POINT,'text-anchor':anchor,'dominant-baseline':'alphabetic',fill:settings.labelcolor});
     t.textContent=row.text;if(settings.rotation)t.setAttribute('transform',`rotate(${-settings.rotation} ${xx} ${yy})`);s.dynamic.append(t);
    }
   }
  });
 }
}
svg.addEventListener('pointerdown',e=>{
 const p=position(e),i=findMap(p);if(i<0||!mode||e.button>2)return;flushWheel();select(i);
 drag={s:state(),start:p,original:navigation.snapshot(),button:e.button,mode,pointer:e.pointerId};
 svg.setPointerCapture(e.pointerId);canvas.classList.add('dragging');
 if(mode==='zoom'){drag.rect=make('rect',{id:'zoom-selection',x:p.x,y:p.y,width:0,height:0});svg.append(drag.rect);}e.preventDefault();
});
svg.addEventListener('pointermove',e=>{
 const p=position(e),i=findMap(p);if(i>=0)showCoordinate(states[i],p);else $('coordinates').textContent='';
 if(!drag)return;const d=drag,s=d.s;
 if(d.mode==='pan')attempt(()=>{
  navigation.restoreViews(d.original);
  if(d.button===2)navigation.zoom(s.index,Math.exp((p.x-d.start.x-(p.y-d.start.y))/180),d.start,axisConstraint);
  else navigation.pan(s.index,p.x-d.start.x,p.y-d.start.y,axisConstraint);
 });
 else if(d.rect){
  const[x,y,w,h]=navigation.viewport(s.index).box,xx=Math.max(x,Math.min(x+w,p.x)),yy=Math.max(y,Math.min(y+h,p.y));
  rect(d.rect,[axisConstraint==='y'?x:Math.min(d.start.x,xx),axisConstraint==='x'?y:Math.min(d.start.y,yy),axisConstraint==='y'?w:Math.abs(xx-d.start.x),axisConstraint==='x'?h:Math.abs(yy-d.start.y)]);
 }
});
function releaseDrag(d){d.rect?.remove();drag=null;canvas.classList.remove('dragging');if(svg.hasPointerCapture(d.pointer))svg.releasePointerCapture(d.pointer);}
function endDrag(){
 if(!drag)return;const d=drag;
 if(d.rect){const r=d.rect,box=['x','y','width','height'].map(k=>+r.getAttribute(k));attempt(()=>navigation.rectangle(d.s.index,box,{out:d.button===2,constraint:axisConstraint}));}
 releaseDrag(d);commit();
}
function cancelDrag(){if(!drag)return;const d=drag;navigation.restoreViews(d.original);releaseDrag(d);redraw();}
svg.addEventListener('pointerup',endDrag);svg.addEventListener('pointercancel',cancelDrag);svg.addEventListener('contextmenu',e=>e.preventDefault());
svg.addEventListener('wheel',e=>{
 const p=position(e),i=findMap(p);if(i<0||drag)return;e.preventDefault();select(i);
 if(attempt(()=>navigation.zoom(i,Math.exp(-Math.max(-100,Math.min(100,e.deltaY))*.004),p,axisConstraint))){clearTimeout(wheelTimer);wheelTimer=setTimeout(()=>{wheelTimer=null;commit();},200);}
},{passive:false});
svg.addEventListener('dblclick',e=>{const p=position(e),i=findMap(p);if(i>=0){flushWheel();select(i);attempt(()=>navigation.zoom(i,2,p,axisConstraint),{push:true});}});
mini.addEventListener('pointerdown',e=>{
 const p=position(e,mini),s=state(),m=s.meta.overview_map;if(!m)return;flushWheel();
 attempt(()=>navigation.center(s.index,[(p.x-m.ox)/m.scale,(m.oy-p.y)/m.scale]),{push:true});
});
function download(blob,extension){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`figure.${extension}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function save(){
 const clone=svg.cloneNode(true);clone.querySelector('#zoom-selection')?.remove();
 const png=$('save-format').value==='png';
 if(png)clone.querySelectorAll(':scope > rect').forEach(n=>{
  // Align touching fill tiles to the same pixel boundary during SVG->canvas.
  // Do not change vector exports, text, linework or stroked rectangles.
  const fill=n.getAttribute('fill'),stroke=n.getAttribute('stroke');
  if(fill&&fill!=='none'&&(!stroke||stroke==='none')&&!n.hasAttribute('transform')){
   const x=+n.getAttribute('x'),y=+n.getAttribute('y'),w=+n.getAttribute('width'),h=+n.getAttribute('height');
   if(![x,y,w,h].every(Number.isFinite))return; // Preserve the percentage-sized Figure background.
   rect(n,[Math.round(x),Math.round(y),Math.round(x+w)-Math.round(x),Math.round(y+h)-Math.round(y)]);
   n.setAttribute('shape-rendering','crispEdges');
  }
 });
 const data=new XMLSerializer().serializeToString(clone),blob=new Blob([data],{type:'image/svg+xml'});
 if(!png){download(blob,'svg');return;}
 const url=URL.createObjectURL(blob),img=new Image();
 img.onload=()=>{const raster=document.createElement('canvas');raster.width=+svg.getAttribute('width');raster.height=+svg.getAttribute('height');raster.getContext('2d').drawImage(img,0,0,raster.width,raster.height);raster.toBlob(b=>{if(b)download(b,'png');},'image/png');URL.revokeObjectURL(url);};
 img.onerror=()=>{URL.revokeObjectURL(url);$('coordinates').textContent='PNG export failed; choose SVG.';};img.src=url;
}
$('home').onclick=restore;$('back').onclick=()=>navigate(-1);$('forward').onclick=()=>navigate(1);$('pan').onclick=()=>setMode('pan');$('zoom').onclick=()=>setMode('zoom');$('save').onclick=save;
$('axes-select').onchange=e=>select(+e.target.value);
document.querySelectorAll('.toolbar button').forEach(button=>{button.addEventListener('mouseenter',()=>{if(!button.disabled)$('coordinates').textContent=button.title;});button.addEventListener('mouseleave',()=>$('coordinates').textContent='');});
svg.addEventListener('pointerleave',()=>{if(!drag)$('coordinates').textContent='';});
document.addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;const key=e.key.toLowerCase();if(['x','y'].includes(key)){axisConstraint=key;return;}if(['h','r','home'].includes(key))restore();else if(['arrowleft','backspace','c'].includes(key))navigate(-1);else if(['arrowright','v'].includes(key))navigate(1);else if(key==='p')setMode('pan');else if(key==='o')setMode('zoom');else if(key==='+'||key==='=')zoomCenter(1.5);else if(key==='-')zoomCenter(1/1.5);else if(key==='s')save();else if(key==='escape')cancelDrag();else if(key==='g'){state().gridVisible=!state().gridVisible;redraw();}else return;e.preventDefault();});
document.addEventListener('keyup',e=>{if(e.key.toLowerCase()===axisConstraint)axisConstraint='';});
// Public inspection hooks make navigation testable without coupling to pixels.
window.azimlib={getState:()=>states.map(s=>({...snapshot(s),box:navigation.viewport(s.index).box,extent:navigation.extent(s.index),history:navigation.history.length,cursor:navigation.cursor,error:lastError,componentErrors:s.componentErrors.slice()})),home:restore,select,zoom:zoomCenter};
redraw();select(0);
})();
