async(page)=>{
 const base=await page.evaluate(()=>new URL('.',location.href).href),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const read=()=>page.evaluate(()=>window.__GARDEN__.state()),assert=(value,message)=>{if(!value)throw new Error(message);};
 await page.goto(base+'?test=1&mode=walk');await page.waitForFunction(()=>window.__GARDEN__?.state().loaded);
 await page.getByRole('button',{name:'Let’s walk together',exact:true}).click();await page.evaluate(()=>window.__GARDEN__.walkTo(0));
 await page.keyboard.down('a');await page.waitForTimeout(700);await page.keyboard.up('a');assert((await read()).walking.lateral===-.12,'Left boundary failed');
 await page.keyboard.down('d');await page.waitForTimeout(1200);await page.keyboard.up('d');assert((await read()).walking.lateral===.12,'Right boundary failed');
 await page.keyboard.down('s');await page.waitForTimeout(450);await page.keyboard.up('s');assert((await read()).walking.z===11.35,'Back boundary failed');
 await page.evaluate(()=>window.__GARDEN__.walkTo(.2));await page.keyboard.down('w');await page.waitForTimeout(500);await page.keyboard.up('w');await page.waitForTimeout(1500);
 const first=await read();assert(first.walking.promptCount===1&&first.walking.handGap<.003,'First response or contact failed');
 await page.waitForTimeout(10000);const idle=await read();assert(idle.walking.speech==='Shall we keep going, my love?','Gentle invitation missing');
 await page.keyboard.down('w');await page.waitForTimeout(500);await page.keyboard.up('w');await page.waitForTimeout(1500);const second=await read();
 assert(second.walking.promptCount===2&&second.walking.speech!==first.walking.speech,'Pause responses did not vary');
 await page.getByRole('button',{name:'Turn music off',exact:true}).click();const chimes=second.walking.chimes;
 await page.keyboard.down('w');await page.waitForTimeout(500);await page.keyboard.up('w');await page.waitForTimeout(1500);assert((await read()).walking.chimes===chimes,'Muted chime played');
 await page.keyboard.down('w');await page.waitForTimeout(350);await page.getByRole('button',{name:'Pause animation',exact:true}).click();await page.keyboard.up('w');await page.waitForTimeout(100);
 const paused=await read();await page.waitForTimeout(500);const held=await read();assert(paused.walking.z===held.walking.z&&held.walking.keys.length===0,'Pause left movement active');assert(held.frames-paused.frames<=2,'Paused scene keeps drawing');
 await page.getByRole('button',{name:'Play animation',exact:true}).click();await page.waitForTimeout(300);assert((await read()).walking.z===held.walking.z,'Movement resumed without input');
 await page.evaluate(()=>window.__GARDEN__.walkTo(.94));await page.getByRole('button',{name:'Walk with me',exact:true}).click();
 const contacts=[];for(let i=0;i<6;i++){await page.waitForTimeout(95);const s=await read();if(s.walking.mode==='walk')contacts.push(...s.walking.feet);}
 assert(contacts.every(f=>f.sole>=f.support-.004),'A shoe clips through its supporting surface');
 await page.waitForFunction(()=>window.__GARDEN__.state().walking.mode==='film',{},{timeout:10000});
 await page.evaluate(()=>window.__GARDEN__.seek(112));await page.waitForTimeout(200);await page.mouse.move(1430,440);await page.waitForTimeout(500);assert((await read()).orbit>.03,'Paused ending orbit failed');
 await page.getByRole('button',{name:'One more time',exact:true}).click();await page.waitForTimeout(200);const replay=await read();assert(replay.walking.mode==='intro'&&replay.walking.promptCount===0&&!replay.finished,'Replay did not reset the walk');
 assert(errors.length===0&&replay.glError===0,'Browser or WebGL error');
 return{errors,first:first.walking.speech,second:second.walking.speech,invitation:idle.walking.speech,mutedChimes:chimes,pauseDraws:held.frames-paused.frames,contactSamples:contacts.length,replay:replay.walking.mode,glError:replay.glError};
}
