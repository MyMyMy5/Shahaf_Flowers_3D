async(page)=>{
 const base=await page.evaluate(()=>new URL(".",location.href).href);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text().slice(0,400));});
 await page.goto(base+'?test=1&mode=film');await page.waitForFunction(()=>window.__GARDEN__?.state().loaded);await page.getByRole('button',{name:"Open when you're ready",exact:true}).click();
 const started=Date.now();await page.waitForFunction(()=>window.__GARDEN__.state().time>=63,{},{timeout:78000,polling:250});
 const middle=await page.evaluate(()=>window.__GARDEN__.state());await page.screenshot({path:'output/playwright/native-full-film-middle.png'});
 await page.waitForFunction(()=>window.__GARDEN__.state().finished,{},{timeout:65000,polling:250});await page.waitForTimeout(400);
 const end=await page.evaluate(()=>window.__GARDEN__.state()),media=await page.evaluate(()=>({time:document.getElementById('music').currentTime,paused:document.getElementById('music').paused}));
 await page.screenshot({path:'output/playwright/native-full-film-ending.png'});
 if(errors.length||end.time!==112||end.glError||media.paused)throw new Error('Full film playback failed');
 return{errors,elapsedSeconds:(Date.now()-started)/1000,middle:{time:middle.time,caption:middle.mode},end:{time:end.time,finished:end.finished,modelTriangles:end.modelTriangles,glError:end.glError},media};
}
