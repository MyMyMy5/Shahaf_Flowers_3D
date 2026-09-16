async(page)=>{
 const base=await page.evaluate(()=>new URL(".",location.href).href);
 const context=await page.context().browser().newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
 const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 const assert=(ok,message)=>{if(!ok)throw new Error(message);};const state=()=>p.evaluate(()=>window.__GARDEN__.state());
 try{
  await p.goto(base+'?test=1&mode=walk');await p.waitForFunction(()=>window.__GARDEN__?.state().loaded);await p.waitForTimeout(1100);
  await p.screenshot({path:'output/playwright/native-phone-cover.png'});
  await p.getByRole('button',{name:'Let’s walk together',exact:true}).click();await p.waitForFunction(()=>window.__GARDEN__.state().walking.mode==='walk',{},{timeout:22000});
  const client=await context.newCDPSession(p),box=await p.locator('#walk-stick').boundingBox(),cx=box.x+box.width/2,cy=box.y+box.height/2;
  const touch=(type,points)=>client.send('Input.dispatchTouchEvent',{type,touchPoints:points});
  await touch('touchStart',[{x:cx,y:cy-31,id:1}]);await p.waitForTimeout(1700);await touch('touchEnd',[]);await p.waitForTimeout(1800);
  const stopped=await state();assert(stopped.walking.z<10.5,'Touch movement failed');assert(stopped.walking.handGap<.003,'Hands separated');assert(stopped.walking.promptCount===1,'Stop response missing');assert(stopped.walking.chimes===1,'Chime did not run');
  await p.screenshot({path:'output/playwright/native-phone-stop.png'});
  await p.getByRole('button',{name:/Look at him/}).click();await p.waitForTimeout(2400);
  await p.screenshot({path:'output/playwright/native-phone-look.png'});const look=await state();assert(look.focus,'Portrait focus did not activate');
  const before=look.frames;await p.waitForTimeout(2500);const after=await state();const fps=(after.frames-before)/2.5;
  await p.getByRole('button',{name:/Look at him/}).click();
  await touch('touchStart',[{x:cx,y:cy-31,id:2}]);await p.waitForTimeout(350);await touch('touchCancel',[]);assert((await state()).walking.stick.y===0,'Touch cancel stuck');
  await p.getByRole('button',{name:'Personalize names and message'}).click();assert((await state()).paused,'Dialog did not pause');await p.getByRole('button',{name:'Close',exact:true}).click();
  await p.evaluate(()=>window.__GARDEN__.walkTo(.97));await p.getByRole('button',{name:'Walk with me',exact:true}).click();
  await p.waitForFunction(()=>window.__GARDEN__.state().walking.mode==='arrival');await p.waitForTimeout(5700);const arrival=await state();
  await p.waitForFunction(()=>window.__GARDEN__.state().walking.mode==='film');await p.waitForTimeout(450);const seated=await state();
  const cameraDelta=Math.hypot(...seated.camera.map((v,i)=>v-arrival.camera[i]));assert(cameraDelta<1,'Phone arrival camera jumped');
  await p.screenshot({path:'output/playwright/native-phone-arrival.png'});
  await p.evaluate(()=>window.__GARDEN__.seek(112));await p.waitForTimeout(1300);await p.screenshot({path:'output/playwright/native-phone-ending.png'});
  await touch('touchStart',[{x:160,y:480,id:3}]);await touch('touchMove',[{x:285,y:480,id:3}]);await touch('touchEnd',[]);await p.waitForTimeout(500);assert((await state()).orbit>.03,'Phone ending orbit failed');
  const layout=await p.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,ending:(()=>{const r=document.getElementById('ending').getBoundingClientRect();return{x:r.x,y:r.y,right:r.right,bottom:r.bottom};})()}));
  assert(!layout.overflow&&layout.ending.x>=0&&layout.ending.right<=390,'Ending layout overflow');
  await p.getByRole('button',{name:'Watch the film',exact:true}).click();await p.waitForTimeout(200);const switched=await state();assert(switched.mode==='cinematic'&&switched.time<1,'Ending switch failed');
  return{errors,stop:{z:stopped.walking.z,text:stopped.walking.speech,chimes:stopped.walking.chimes,handGap:stopped.walking.handGap},emulatedPortraitFps:fps,cameraDelta,layout,switched:switched.mode,parts:stopped.walking.parts};
 }finally{await context.close();}
}
