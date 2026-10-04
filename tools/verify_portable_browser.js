/* Headless integration of the local exported viewer in a fresh browser context. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'../gallery');
const artifacts=path.resolve(process.argv[2]||path.join(__dirname,'../browser-qa'));
fs.mkdirSync(artifacts,{recursive:true});
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} != ${b}`);
const eq=(a,b)=>a.forEach((v,i)=>near(v,b[i]));

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.AZIMLIB_BROWSER_EXECUTABLE||undefined,headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1200,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  async function load(name){await page.goto('file:///'+path.join(root,name+'.html').replaceAll('\\','/'));await page.waitForFunction(()=>!!window.azimlib);}
  const state=()=>page.evaluate(()=>window.azimlib.getState());
  async function point(s,fx=.5,fy=.5){
   const svg=page.locator('#canvas > svg'),b=await svg.boundingBox(),size=await svg.evaluate(el=>[+el.getAttribute('width'),+el.getAttribute('height')]);
   return {x:b.x+(s.box[0]+s.box[2]*fx)*b.width/size[0],y:b.y+(s.box[1]+s.box[3]*fy)*b.height/size[1]};
  }
  await load('linked-navigation');const initial=await state();assert.equal(initial.length,4);
  assert.equal(await page.locator('#overview').isVisible(),false);
  await page.screenshot({path:path.join(root,'linked-navigation-viewer.png'),fullPage:true});
  await page.locator('#zoom').click();let start=await point(initial[0],.25,.25),end=await point(initial[0],.75,.75);
  await page.mouse.move(start.x,start.y);await page.mouse.down();await page.mouse.move(end.x,end.y,{steps:5});await page.mouse.up();
  let zoomed=await state();zoomed.forEach(s=>eq(s.extent,zoomed[0].extent));assert.equal(zoomed[0].history,2);
  assert.ok(zoomed[0].extent[1]-zoomed[0].extent[0]<initial[0].extent[1]-initial[0].extent[0]);
  const beforePan=zoomed.map(s=>s.extent);
  await page.locator('#pan').click();start=await point(zoomed[2]);
  await page.mouse.move(start.x,start.y);await page.mouse.down();await page.mouse.move(start.x+20,start.y-10,{steps:3});await page.mouse.up();
  let moved=await state();moved.forEach(s=>eq(s.extent,moved[0].extent));assert.equal(moved[0].history,3);
  assert.ok(Math.abs(moved[0].extent[0]-beforePan[0][0])>1e-3);
  await page.screenshot({path:path.join(root,'linked-navigation-zoomed-viewer.png'),fullPage:true});
  await page.locator('#back').click();(await state()).forEach((s,i)=>eq(s.extent,beforePan[i]));
  await page.locator('#forward').click();(await state()).forEach((s,i)=>eq(s.extent,moved[i].extent));
  await page.locator('#home').click();(await state()).forEach((s,i)=>eq(s.extent,initial[i].extent));
  await page.locator('#back').click();(await state()).forEach((s,i)=>eq(s.extent,moved[i].extent));
  // Cursor readout follows the new transform.
  let cursor=await point((await state())[0],.4,.6);await page.mouse.move(cursor.x,cursor.y);
  assert.match(await page.locator('#coordinates').textContent(),/^x=-?\d+\.\d+  y=-?\d+\.\d+$/);
  // A cancelled gesture restores every linked member and does not push history.
  const checkpoint=await state();start=await point(checkpoint[1]);
  await page.mouse.move(start.x,start.y);await page.mouse.down();await page.mouse.move(start.x+15,start.y+8,{steps:3});
  await page.locator('#canvas > svg').dispatchEvent('pointercancel',{pointerId:1});await page.mouse.up();
  (await state()).forEach((s,i)=>{eq(s.extent,checkpoint[i].extent);assert.equal(s.history,checkpoint[i].history);});
  // Wheel followed immediately by Home must flush its history entry first.
  await page.mouse.move(start.x,start.y);await page.mouse.wheel(0,-100);await page.waitForTimeout(250);
  let wheeled=await state();assert.ok(wheeled[0].history>=checkpoint[0].cursor+2);
  await page.locator('#home').click();(await state()).forEach((s,i)=>eq(s.extent,initial[i].extent));
  // Locator click changes the common projected center, never creates a default minimap.
  await page.evaluate(()=>window.azimlib.zoom(2));
  const focus=await page.locator('#canvas > svg').evaluate(svg=>{const m=JSON.parse(document.getElementById('map-data').textContent)[0].overview_map;return {m,rect:svg.getBoundingClientRect().toJSON(),width:+svg.getAttribute('width'),height:+svg.getAttribute('height')};});
  const [mx,my,mw,mh]=focus.m.box;await page.mouse.click(focus.rect.x+(mx+mw*.45)*focus.rect.width/focus.width,focus.rect.y+(my+mh*.6)*focus.rect.height/focus.height);
  const located=await state();located.forEach(s=>eq(s.extent,located[0].extent));
  // SVG and PNG save only the current canvas, with no viewer UI.
  await page.locator('#save-format').selectOption('svg');
  let downloadPromise=page.waitForEvent('download');await page.locator('#save').click();
  let download=await downloadPromise;await download.saveAs(path.join(artifacts,'portable-browser.svg'));
  const saved=fs.readFileSync(path.join(artifacts,'portable-browser.svg'),'utf8');assert.ok(saved.includes('data-map-content'));assert.ok(!saved.includes('<script'));assert.ok(!saved.includes('Figure navigation'));
  await page.locator('#save-format').selectOption('png');downloadPromise=page.waitForEvent('download');await page.locator('#save').click();
  download=await downloadPromise;await download.saveAs(path.join(artifacts,'portable-browser.png'));
  assert.ok(fs.statSync(path.join(artifacts,'portable-browser.png')).size>1000);
  const bands=await page.locator('#canvas > svg').evaluate(svg=>{
   const meta=JSON.parse(document.getElementById('map-data').textContent),bottom=Math.max(...meta.filter(m=>!m.inset).map(m=>m.box[1]+m.box[3]));
   return [...svg.querySelectorAll(':scope > rect')].map(r=>({x:+r.getAttribute('x'),y:+r.getAttribute('y'),width:+r.getAttribute('width'),height:+r.getAttribute('height'),fill:r.getAttribute('fill')})).filter(r=>r.y>bottom&&r.width<10&&r.height>15&&r.fill&&r.fill!=='none');
  });
  assert.ok(bands.length>100);fs.writeFileSync(path.join(artifacts,'portable-browser-raster.json'),JSON.stringify(bands));
  await load('linked-groups');const grouped=await state();
  assert.equal(await page.locator('#overview').isVisible(),false);
  await page.locator('#canvas').focus();await page.keyboard.down('x');await page.keyboard.press('+');await page.keyboard.up('x');
  const changed=await state();eq(changed[0].extent.slice(0,2),changed[2].extent.slice(0,2));
  eq(changed[1].extent,grouped[1].extent);eq(changed[3].extent,grouped[3].extent);
  changed.forEach((s,i)=>eq(s.extent.slice(2),grouped[i].extent.slice(2)));
  await page.screenshot({path:path.join(root,'linked-groups-viewer.png'),fullPage:true});
  await page.locator('#back').click();(await state()).forEach((s,i)=>eq(s.extent,grouped[i].extent));
  // Explicit scale, north and rose recompose/reanchor in physical screen units.
  await load('portable-components');const componentsInitial=await state();
  await page.evaluate(()=>window.azimlib.zoom(2));
  const componentsZoom=await state();componentsZoom.forEach(s=>assert.deepEqual(s.componentErrors,[]));
  for(let i=0;i<2;i++)for(const kind of ['scale','north','compass'])assert.equal(await page.locator(`[data-dynamic-components="${i}"] [data-component="${kind}"]`).count(),1);
  const scaleLength=await page.locator('[data-dynamic-components="0"] [data-component="scale"]').getAttribute('data-length');
  const before=await page.locator('[data-dynamic-components="0"] [data-component="north"]').boundingBox();
  await page.evaluate(()=>window.azimlib.zoom(2));
  assert.ok(+(await page.locator('[data-dynamic-components="0"] [data-component="scale"]').getAttribute('data-length'))<+scaleLength);
  const after=await page.locator('[data-dynamic-components="0"] [data-component="north"]').boundingBox();near(before.width,after.width);near(before.height,after.height);
  await page.screenshot({path:path.join(root,'portable-components-zoomed-viewer.png'),fullPage:true});
  await page.locator('#home').click();(await state()).forEach((s,i)=>eq(s.extent,componentsInitial[i].extent));
  assert.equal(await page.locator('[data-component="scale"]').count(),0);
  await page.locator('#back').click();assert.equal(await page.locator('[data-component="scale"]').count(),2);
  await page.locator('#pan').click();const cp=await point((await state())[0]);
  await page.mouse.move(cp.x,cp.y);await page.mouse.down();await page.mouse.move(cp.x+20,cp.y+12,{steps:3});await page.mouse.up();
  (await state()).forEach(s=>assert.deepEqual(s.componentErrors,[]));
  await page.locator('#save-format').selectOption('svg');downloadPromise=page.waitForEvent('download');await page.locator('#save').click();
  download=await downloadPromise;await download.saveAs(path.join(artifacts,'portable-components-browser.svg'));
  assert.ok(fs.readFileSync(path.join(artifacts,'portable-components-browser.svg'),'utf8').includes('data-component="scale"'));
  await page.locator('#save-format').selectOption('png');downloadPromise=page.waitForEvent('download');await page.locator('#save').click();
  download=await downloadPromise;await download.saveAs(path.join(artifacts,'portable-components-browser.png'));
  await load('portable-fixed-scale');await page.evaluate(()=>window.azimlib.zoom(100));
  assert.match((await state())[0].componentErrors[0],/Requested scale/);assert.match(await page.locator('#coordinates').textContent(),/^Scale:/);
  assert.equal(await page.locator('[data-component="scale"]').count(),0);assert.equal(await page.locator('[data-component="north"]').count(),1);
  await page.locator('#home').click();assert.deepEqual((await state())[0].componentErrors,[]);
  await load('linked-groups');await page.evaluate(()=>window.azimlib.zoom(2));assert.equal(await page.locator('[data-component]').count(),0);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({browser:'Chromium headless / fresh Playwright context',scenarios:['rectangle','pan','figure history','Home','cursor','pointer cancel','wheel','overview','SVG save','PNG save','column groups','x constraint','scale recalculation','fixed orientation size','components Home/history','components pan','components SVG export','components PNG export','explicit scale overflow','optional absence'],pageErrors:errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
