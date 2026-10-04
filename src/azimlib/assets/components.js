/* Portable cartographic components, using our projections and font metrics. */
(function(root){'use strict';
const nav=typeof module==='object'&&module.exports?require('./navigation.js'):root.AzimlibNavigation;
const RAD=Math.PI/180;
function width(text,metrics,size){
 if(!metrics)return text.length*size*.62;
 let previous=null,total=0;
 for(const char of text){const [glyph,advance]=metrics.chars[char]||metrics.chars['?'];total+=advance+(metrics.kern[`${previous},${glyph}`]||0);previous=glyph;}
 return total*size/metrics.units;
}
function baseline(text,metrics,size,alignment){
 const values=[...text].filter(c=>!c.match(/\s/)).map(c=>metrics?.bounds[c]||[0,(metrics?.units||1)*.75]);
 const [ascent,descent]=metrics?.vertical||[.8,.2];
 const low=Math.min(-descent*size,metrics&&values.length?Math.min(...values.map(v=>v[0]))*size/metrics.units:0);
 const high=Math.max(ascent*size,metrics&&values.length?Math.max(...values.map(v=>v[1]))*size/metrics.units:0);
 return alignment==='top'?high:alignment==='middle'?(low+high)/2:alignment==='bottom'?low:0;
}
function textPlan(text,metrics,size,ha,va,rotation=0,mode='default'){
 const lines=String(text).replace(/\r\n?/g,'\n').split('\n'),[a,d,g]=metrics?.vertical||[.8,.2,.2];
 const rows=lines.map(line=>{
  const ink=[...line].filter(c=>!c.match(/\s/)).map(c=>metrics?.bounds[c]||[0,(metrics?.units||1)*.75]);
  const high=metrics&&ink.length?Math.max(...ink.map(b=>b[1]))*size/metrics.units:0;
  const low=metrics&&ink.length?Math.min(...ink.map(b=>b[0]))*size/metrics.units:0;
  const gap=lines.length>1?g*size/2:0;
  return {text:line,width:width(line,metrics,size),ascent:Math.max(a*size,high)+gap,descent:Math.max(d*size,-low)+gap};
 });
 const total=rows.reduce((v,r)=>v+r.ascent+r.descent,0),first=rows[0].ascent,last=rows.at(-1).descent;
 let cursor={top:first,middle:first-total/2,bottom:first-total,alphabetic:first-total+last}[va];
 rows.forEach((r,i)=>{if(i)cursor+=rows[i-1].descent+r.ascent;r.y=cursor;});
 const w=Math.max(...rows.map(r=>r.width)),left=-({start:0,middle:.5,end:1}[ha])*w,top=rows[0].y-first;
 const angle=-rotation*RAD,c=Math.cos(angle),s=Math.sin(angle);
 const points=[[left,top],[left+w,top],[left+w,top+total],[left,top+total]].map(([x,y])=>[x*c-y*s,x*s+y*c]);
 const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),l=Math.min(...xs),r=Math.max(...xs),t=Math.min(...ys),b=Math.max(...ys);
 let align=ha,vertical=va,dx=0,dy=0;
 const publicAngle=((rotation%360)+360)%360;
 if(mode==='xtick'){
  const central=publicAngle<=10||publicAngle>=350||publicAngle>=85&&publicAngle<=95||publicAngle>=170&&publicAngle<=190||publicAngle>=265&&publicAngle<=275;
  const first=publicAngle>10&&publicAngle<85||publicAngle>190&&publicAngle<265;
  align=central?'middle':first?(va==='bottom'?'start':'end'):(va==='bottom'?'end':'start');
 }else if(mode==='ytick'){
  const central=publicAngle<=10||publicAngle>=350||publicAngle>=170&&publicAngle<=190||publicAngle>=80&&publicAngle<=100||publicAngle>=260&&publicAngle<=280;
  const first=publicAngle>190&&publicAngle<260||publicAngle>10&&publicAngle<80;
  vertical=central?'middle':first?(ha==='start'?'alphabetic':'top'):(ha==='start'?'top':'alphabetic');
 }
 if(mode!=='anchor'){
  dx=-({start:l,middle:(l+r)/2,end:r}[align]);
  dy=-({top:t,middle:(t+b)/2,bottom:b,alphabetic:b-last}[vertical]);
 }
 return {rows:rows.map(row=>({text:row.text,x:dx-row.y*s,y:dy+row.y*c})),box:[l+dx,t+dy,r-l,b-t]};
}
function general(value){
 const rounded=+value.toPrecision(6),exponent=Math.floor(Math.log10(Math.abs(rounded)));
 if(rounded&&(exponent<-4||exponent>=6)){
  const [mantissa,power]=rounded.toExponential(5).split('e');
  return mantissa.replace(/\.?0+$/,'')+'e'+(+power<0?'-':'+')+String(Math.abs(+power)).padStart(2,'0');
 }
 return String(rounded);
}
function anchor(box,loc,w,h,pad){
 const[x,y,width,height]=box;return [loc.includes('left')?x+pad:x+width-w-pad,loc.includes('upper')?y+pad:y+height-h-pad];
}
function distance(a,b){
 const p=a[1]*RAD,q=b[1]*RAD,v=Math.sin((q-p)/2)**2+Math.cos(p)*Math.cos(q)*Math.sin((b[0]-a[0])*RAD/2)**2;
 return 2*6371008.8*Math.asin(Math.sqrt(Math.max(0,Math.min(1,v))));
}
function scale(component,meta,view){
 const o=component.options,metrics=component.metrics,ratio=meta.pixel_ratio||1,P=100/72*ratio,fs=o.fontsize*P;
 if(!['equirectangular','mercator'].includes(meta.projection.name))throw new Error('Scale recomposition requires a continuous cylindrical map');
 const maxwidth=Math.min(view.box[2]*.25,180*ratio),factor={m:1,km:1000,mi:1609.344}[o.units];
 let boxheight=fs*3.4,barOffset=fs*1.45,labels=[],compact=false,measured=[];
 const verticalpad=fs*.4;
 function height(text){return baseline(text,metrics,fs,'top')-baseline(text,metrics,fs,'bottom');}
 function sizeVertical(){
  const captionheight=Math.max(...(labels.length?labels.map(([,t])=>height(t)):[height('0')]));
  barOffset=verticalpad+captionheight+fs*.3;
  boxheight=barOffset+fs*.48+verticalpad+(compact?0:fs*.37+height(o.units));
 }
 sizeVertical();
 function placement(w){
  let left=-.3*P,right=w+.3*P;
  for(const [fraction,textwidth] of measured){left=Math.min(left,fraction*w-textwidth/2);right=Math.max(right,fraction*w+textwidth/2);}
  if(!compact){const uw=width(o.units,metrics,fs);left=Math.min(left,(w-uw)/2);right=Math.max(right,(w+uw)/2);}
  const pad=fs*.5+Math.max(-left,right-w),fw=w+2*pad,[bx,by]=anchor(view.box,o.loc,fw,boxheight,fs*.5);
  return {bx,by,x:bx+pad,y:by+barOffset,framewidth:fw};
 }
 function inverse(x,y){
  const pr=meta.projection,result=nav.inverse(pr,(x-view.ox)/view.scale,(view.oy-y)/view.scale);
  if(!result||!result.every(Number.isFinite)||Math.abs(result[0]-(pr.central_longitude||0))>180+1e-8||Math.abs(result[1])>(pr.name==='mercator'?pr.max_latitude||85.0511287798066:90)+1e-8)
   throw new Error('Scale anchor lies outside the projection');
  return result;
 }
 function measure(w){const {x,y}=placement(w);return distance(inverse(x,y),inverse(x+w,y))/factor;}
 function nice(available){const power=10**Math.floor(Math.log10(available));return Math.max(...[.1,.2,.5,1,2,5].map(v=>power*v).filter(v=>v<=available));}
 let available=measure(maxwidth);
 if(!(available>0))throw new Error('Scale has no measurable geographic span');
 let length=o.length??nice(available),w,fit=false;
 for(const count of [3,2,1]){
  compact=count===1;
  for(let retries=0;retries<50;retries++){
   const full=[[0,'0'],[.5,general(length/2)],[1,general(length)]];
   labels=count===3?full:count===2?[full[0],full[2]]:[[.5,`${general(length)} ${o.units}`]];
   measured=labels.map(([f,t])=>[f,width(t,metrics,fs)]);sizeVertical();available=measure(maxwidth);
   if(!(available>0))throw new Error('Scale has no measurable geographic span');
   if(o.length==null&&length>available){length=nice(available);continue;}
   break;
  }
  if(length>available)continue;
  let lo=0,hi=maxwidth;
  for(let i=0;i<36;i++){const mid=(lo+hi)/2;if(measure(mid)>length)hi=mid;else lo=mid;}
  w=(lo+hi)/2;const gap=Math.max(2*P,fs*.3);
  if(measured.slice(1).every(([b,bw],i)=>measured[i][0]*w+measured[i][1]/2+gap<=b*w-bw/2)){fit=true;break;}
 }
 if(!fit)throw new Error('Requested scale is wider than its allotted space; use a shorter length');
 const {bx,by,x,y,framewidth}=placement(w),items=[];
 if(o.frameon!==false){
  const r=2*P,corners=[];
  for(const[cx,cy,start] of [[bx+framewidth-r,by+r,-90],[bx+framewidth-r,by+boxheight-r,0],[bx+r,by+boxheight-r,90],[bx+r,by+r,180]])
   for(let i=0;i<7;i++)corners.push([cx+r*Math.cos((start+i*90/6)*RAD),cy+r*Math.sin((start+i*90/6)*RAD)]);
  items.push({kind:'path',points:corners,fill:o.facecolor||'white',stroke:o.edgecolor||'#cccccc',stroke_width:(o.linewidth??.8)*P,opacity:o.framealpha??.8});
 }
 for(let i=0;i<2;i++)items.push({kind:'rect',x:x+i*w/2,y,width:w/2,height:fs*.48,fill:i===0?o.color:'white',stroke:o.color,stroke_width:.6*P});
 for(const[f,t]of labels)items.push({kind:'text',x:x+f*w,y:y-fs*.3+baseline(t,metrics,fs,'bottom'),text:t,size:fs,fill:o.color,stroke:'none',stroke_width:0,opacity:1});
 if(!compact)items.push({kind:'text',x:x+w/2,y:y+fs*.85+baseline(o.units,metrics,fs,'top'),text:o.units,size:fs,fill:o.color,stroke:'none',stroke_width:0,opacity:1});
 return {items,length,width:w,labels,compact,frame:[bx,by,framewidth,boxheight],bar:[x,y,w,fs*.48],units:o.units};
}
function orientationOffset(component,meta,view){
 const loc=component.options.loc,[x,y,w,h]=view.box,[ox,oy,ow,oh]=meta.box;
 return [x-ox+(loc.includes('right')?w-ow:0),y-oy+(loc.includes('lower')?h-oh:0)];
}
const api={scale,width,baseline,textPlan,general,distance,orientationOffset};root.AzimlibComponents=api;
if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
