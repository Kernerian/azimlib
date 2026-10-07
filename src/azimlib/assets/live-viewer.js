/* Original live input protocol; same-origin loopback session, no CDN/framework. */
(()=>{'use strict';const canvas=document.getElementById('canvas'),status=document.getElementById('status');
let revision=-1,held=null,chain=Promise.resolve(),stopped=false,lastMotion=null,raf=null;
function send(data){chain=chain.then(()=>fetch('event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})).then(r=>{if(!r.ok)throw Error('Input rejected');}).catch(e=>{status.textContent=e.message;held=null;});}
function point(e){const svg=canvas.querySelector('svg'),r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*Number(svg?.getAttribute('width')||r.width)/r.width,y:(e.clientY-r.top)*Number(svg?.getAttribute('height')||r.height)/r.height};}
function input(name,e,extras={}){send({op:'input',name,...point(e),...extras});}
function flushMotion(){if(lastMotion){send(lastMotion);lastMotion=null;}raf=null;}
document.querySelectorAll('[data-command]').forEach(b=>b.onclick=()=>send({op:'command',name:b.dataset.command}));
canvas.oncontextmenu=e=>e.preventDefault();
canvas.onpointerdown=e=>{held=e.button+1;canvas.setPointerCapture(e.pointerId);canvas.focus();input('button_press_event',e,{button:held});};
canvas.onpointermove=e=>{lastMotion={op:'input',name:'motion_notify_event',...point(e),buttons:[1,2,3].filter((b,i)=>e.buttons&[1,4,2][i])};if(!raf)raf=requestAnimationFrame(flushMotion);};
canvas.onpointerup=e=>{flushMotion();input('button_release_event',e,{button:e.button+1});held=null;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);};
canvas.onlostpointercapture=()=>{if(held){send({op:'input',name:'button_release_event',button:held});held=null;}};
canvas.onwheel=e=>{e.preventDefault();input('scroll_event',e,{step:e.deltaY<0?1:-1});};
canvas.onkeydown=e=>{const command={h:'home',p:'pan',o:'zoom',ArrowLeft:'back',ArrowRight:'forward'}[e.key];if(command){e.preventDefault();send({op:'command',name:command});}send({op:'input',name:'key_press_event',key:e.key.slice(0,32)});};
async function poll(){if(stopped)return;try{const response=await fetch('snapshot');if(!response.ok)throw Error('Viewer closed');const s=await response.json();if(s.revision!==revision){revision=s.revision;canvas.innerHTML=s.svg;canvas.style.width=s.width+'px';canvas.style.height=s.height+'px';document.querySelector('[data-command=back]').disabled=!s.back;document.querySelector('[data-command=forward]').disabled=!s.forward;document.querySelectorAll('[data-command=pan],[data-command=zoom]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.command===s.mode));}status.textContent=s.error||s.coordinates||s.mode||'';}catch(e){status.textContent=e.message;stopped=true;}if(!stopped)setTimeout(poll,100);}
let lastSize='';new ResizeObserver(()=>{const r=canvas.getBoundingClientRect(),width=Math.round(r.width-2),height=Math.round(r.height-2),key=width+','+height;if(width>=60&&height>=60&&width<=4096&&height<=4096&&key!==lastSize){lastSize=key;send({op:'resize',width,height});}}).observe(canvas);
window.addEventListener('pagehide',()=>{stopped=true;if(raf)cancelAnimationFrame(raf);});poll();})();
