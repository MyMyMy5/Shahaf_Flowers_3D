async(page)=>{
 const base=await page.evaluate(()=>new URL(".",location.href).href);
 const results=[];
 for(const [width,height,mobile]of[[1440,900,false],[390,844,true],[375,667,true],[844,390,true]]){
  const c=await page.context().browser().newContext({viewport:{width,height},deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile}),p=await c.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text().slice(0,500));});
  try{
   await p.goto(base+'?test=1&mode=walk');await p.waitForFunction(()=>window.__GARDEN__?.state().loaded);await p.waitForTimeout(1100);
   await p.screenshot({path:`output/playwright/final-cover-${width}.png`});
   await p.getByRole('button',{name:'Let’s walk together',exact:true}).click();await p.evaluate(()=>window.__GARDEN__.walkTo(.3));
   await p.getByRole('button',{name:/Look at him/}).click();await p.waitForTimeout(2400);await p.screenshot({path:`output/playwright/final-look-${width}.png`});
   await p.evaluate(()=>window.__GARDEN__.seek(38));await p.waitForTimeout(1400);await p.screenshot({path:`output/playwright/final-cafe-${width}.png`});
   await p.evaluate(()=>window.__GARDEN__.seek(112));await p.waitForTimeout(1400);await p.screenshot({path:`output/playwright/final-ending-${width}.png`});
   const s=await p.evaluate(()=>window.__GARDEN__.state()),layout=await p.evaluate(()=>{const r=document.getElementById('ending').getBoundingClientRect();return{overflow:document.documentElement.scrollWidth>innerWidth,ending:{left:r.left,right:r.right,top:r.top,bottom:r.bottom}};});
   if(errors.length||s.glError||layout.overflow||layout.ending.left<0||layout.ending.right>width)throw new Error(`Layout ${width} failed`);
   results.push({width,height,errors,modelTriangles:s.modelTriangles,glError:s.glError,layout});
  }finally{await c.close();}
 }
 return results;
}
