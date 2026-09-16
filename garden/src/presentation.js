import {END,FINALE,ORBIT,chapters,captions,clamp} from './story.js';
const $=id=>document.getElementById(id);
const pristine='<!doctype html>\n'+document.documentElement.outerHTML;
const defaultLine="All my love, my little princess.\nHere's to our next chapter.";
export function createPresentation(callbacks={}){
 let config;try{config=JSON.parse($('love-config').textContent);}catch{config={};}
 config={herName:String(config.herName||'Shahaf').slice(0,50),yourName:String(config.yourName||'').slice(0,50),lastLine:String(config.lastLine||defaultLine).slice(0,180),preferredMode:config.preferredMode==='walk'?'walk':'film'};
 const state={started:false,paused:false,finished:false,time:0,clock:0,mode:'cinematic',config,ready:false};
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),music=$('music');music.volume=.72;
 let soundEnabled=false,soundChosen=false,audioId=0,captionKey=null,modalPaused=false,toastTimer;
 function toast(text){$('toast').textContent=text;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),3200);}
 function soundUI(){const on=soundEnabled;$('sound').setAttribute('aria-pressed',String(on));$('sound').setAttribute('aria-label',on?'Turn music off':'Turn music on');$('sound').title=on?'Turn music off':'Turn music on';$('sound').querySelector('.control-word').textContent=on?'sound on':'sound off';callbacks.onSound?.(on);}
 async function syncAudio(){const id=++audioId;if(!soundEnabled||state.paused||document.hidden){music.pause();return;}try{await music.play();}catch(e){if(id!==audioId||e.name==='AbortError')return;soundEnabled=false;soundUI();toast('Tap sound again to start the music.');}}
 function pause(value){state.paused=!!value;document.body.classList.toggle('paused',state.paused);$('pause').setAttribute('aria-label',state.paused?'Play animation':'Pause animation');$('pause').title=state.paused?'Play':'Pause';callbacks.onPause?.(state.paused);syncAudio();}
 function start(){if(!state.ready)return;Object.assign(state,{started:true,paused:false,finished:false,time:0,clock:0,mode:'cinematic'});captionKey=null;callbacks.onStart?.(state);
  $('cover').classList.add('departed');$('cover').inert=true;$('pause').classList.remove('initially-hidden');$('transport').classList.remove('initially-hidden');$('ending').hidden=true;
  document.body.classList.remove('paused');$('pause').setAttribute('aria-label','Pause animation');music.currentTime=0;if(!soundChosen)soundEnabled=true;soundUI();syncAudio();}
 function seek(t,pauseAfter=false){if(!state.started)start();callbacks.onSeek?.();state.mode='cinematic';state.time=clamp(t,0,END);state.finished=state.time>=END;captionKey=null;if(pauseAfter)pause(true);draw();}
 function applyNames(){document.title=config.herName?`For ${config.herName}`:'For you';document.querySelector('.tiny-signature').textContent=(config.yourName||'me')+' + '+(config.herName||'you')+' ♡';$('her-name').value=config.herName;$('your-name').value=config.yourName;$('last-line').value=config.lastLine;document.querySelector('#cover p').textContent=config.herName?`${config.herName}, this is my kind of love letter.`:'This is my kind of love letter.';captionKey=null;callbacks.onNamesChanged?.();}
 function readForm(){config.herName=$('her-name').value.trim().slice(0,50);config.yourName=$('your-name').value.trim().slice(0,50);config.lastLine=$('last-line').value.trim().slice(0,180)||defaultLine;applyNames();}
 const buttons=chapters.map((c,i)=>{const b=document.createElement('button');b.innerHTML='<span></span>';b.title=c.title;b.setAttribute('aria-label',`Chapter ${i+1}: ${c.title}`);b.onclick=()=>seek(c.at+.15);$('chapters').append(b);return b;});
 $('chapter-total').textContent=String(chapters.length).padStart(2,'0');
 function draw(){
  if(!state.started)return;
  if(callbacks.drawCaption?.(state))return;
  const t=state.time,row=captions.find(c=>t>=c[0]&&t<c[1]);
  const item=t>=FINALE?{key:'final',title:'I love you.',subtitle:config.lastLine,style:'final',kicker:config.herName?`FOR ${config.herName.toUpperCase()}`:'ALWAYS, MY LOVE'}:row?{key:row[0],title:row[2],subtitle:row[3],style:row[4]||'',kicker:''}:null;
  const key=item?String(item.key)+config.herName+config.lastLine:'';
  if(key!==captionKey){captionKey=key;$('caption').classList.remove('visible');if(item){$('caption-title').textContent=item.title;$('caption-subtitle').textContent=item.subtitle;$('caption-kicker').textContent=item.kicker;$('caption').dataset.style=item.style;requestAnimationFrame(()=>$('caption').classList.add('visible'));}}
  const index=t>=END?chapters.length-1:Math.max(0,chapters.findIndex(c=>t>=c.at&&t<c.end));
  $('chapter-number').textContent=String(index+1).padStart(2,'0');$('chapter-title').textContent=chapters[index].title;
  buttons.forEach((b,i)=>{const fill=clamp((t-chapters[i].at)/(chapters[i].end-chapters[i].at));b.setAttribute('aria-current',String(index===i));b.style.setProperty('--fill',fill.toFixed(4));b.firstElementChild.style.transform=`scaleX(${fill})`;});
  $('ending').hidden=t<ORBIT;$('experience').classList.toggle('orbit-enabled',t>=ORBIT);
 }
 function tick(dt){if(document.hidden||state.paused)return;if(state.started){state.clock+=dt;if(callbacks.advance?.(dt,state)!==true&&!state.finished){state.time=Math.min(END,state.time+dt);state.finished=state.time>=END;}}else if(!reduced.matches)state.clock+=dt;}
 $('begin').disabled=true;$('begin').onclick=start;$('again').onclick=start;$('pause').onclick=()=>pause(!state.paused);
 $('sound').onclick=()=>{soundChosen=true;soundEnabled=!soundEnabled;soundUI();syncAudio();};
 $('settings').onclick=()=>{modalPaused=state.paused;pause(true);applyNames();$('personalize').showModal();};
 $('close-settings').onclick=()=>$('personalize').close();$('personalize').addEventListener('close',()=>pause(modalPaused));
 $('personalize-form').onsubmit=e=>{e.preventDefault();readForm();$('personalize').close();toast('Made a little more yours.');};
 $('personalize').addEventListener('click',e=>{if(e.target!==$('personalize'))return;const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();});
 $('save-file').onclick=async()=>{readForm();const button=$('save-file');button.disabled=true;try{
   const html=window.__GARDEN_PACKED__?pristine:await fetch('./standalone.html').then(r=>{if(!r.ok)throw new Error('Download not ready');return r.text();});
   const json=JSON.stringify(config).replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/&/g,'\\u0026');
   const personalized=html.replace(/(<script id="love-config" type="application\/json">)[\s\S]*?(<\/script>)/,(_,open,close)=>open+json+close);
   const url=URL.createObjectURL(new Blob([personalized],{type:'text/html;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download='our-little-garden.html';link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);toast('Her garden is saved, with the music.');
  }catch(e){toast('The download could not finish. Please try again.');console.error(e);}finally{button.disabled=false;}};
 document.addEventListener('keydown',e=>{if($('personalize').open||e.target.matches('input,textarea,button')||callbacks.onKey?.(e))return;if(e.code==='Space'&&state.started){e.preventDefault();pause(!state.paused);}if(state.mode!=='cinematic'||!state.started||e.repeat)return;if(e.key==='ArrowRight'){e.preventDefault();const next=chapters.find(c=>c.at>state.time+.5);if(next)seek(next.at+.1);}if(e.key==='ArrowLeft'){e.preventDefault();const i=state.time>=END?chapters.length-1:chapters.findIndex(c=>state.time>=c.at&&state.time<c.end);seek(chapters[Math.max(0,i-1)].at+.1);}});
 document.addEventListener('visibilitychange',()=>{syncAudio();callbacks.onVisibility?.(!document.hidden);});
 $('reduced-note').hidden=!reduced.matches;reduced.addEventListener('change',()=>{$('reduced-note').hidden=!reduced.matches;if(reduced.matches)pause(true);});
 $('retry').onclick=()=>location.reload();applyNames();
 return {state,reduced,start,seek,pause,draw,tick,toast,isSoundOn:()=>soundEnabled,ready(){state.ready=true;$('begin').disabled=false;$('loading').classList.add('ready');},error(error){$('loading').classList.add('ready');$('error').hidden=false;$('error').querySelector('p').textContent='The garden could not load. Reload to try again.';console.error(error);}};
}
