import * as THREE from 'three';
import {between,mix,clamp,cameraAt} from './story.js';
const $=id=>document.getElementById(id),V=THREE.Vector3,Q=THREE.Quaternion;
const UP=new V(0,1,0),FORWARD=new V(0,0,-1),IDENTITY=new Q();
const START=11.35,END=3.15,ARRIVAL=6.2;
const center=z=>Math.sin(z*.27)*.45;
function ground(x,z){const r=Math.hypot(x,z);return -.14+Math.max(0,(r-4.4)/10)*(.13*Math.sin(x*.7)+.10*Math.cos(z*.6));}
function floorAt(x,z){
 if(Math.hypot(x,z+1.2)<4.0&&z<=2.9)return .243;
 if(z<=3.175&&z>=2.5&&Math.abs(x)<1.05)return .17;
 if(z<=3.405&&z>=2.73&&Math.abs(x)<1.12)return .115;
 if(z<=3.635&&z>=2.96&&Math.abs(x)<1.19)return .06;
 return ground(x,z)+.116;
}
const lines=[
 'A whole garden, and you’re still my favourite part.',
 'I like this. Going through life, holding your hand.',
 'Take your time, beautiful. I’m enjoying the view.',
 'There’s that smile. The one I keep falling for.',
 'Little moments like this. I want so many more of them.',
 'You make even an ordinary walk feel special.',
 'One day, real flowers. A real evening. The two of us.',
 'We don’t have to rush the good things.',
 'I’m excited for all the little things we haven’t done yet.',
 'That’s my favourite person, right there.',
 'More patience. More laughter. More lovely days with you.',
 'I made all of this just to make you smile.'
];
function bend(a,b,upper,lower,preferred){const direction=b.clone().sub(a).normalize(),distance=clamp(a.distanceTo(b),.01,upper+lower-.001),along=(upper*upper-lower*lower+distance*distance)/(2*distance),perpendicular=preferred.clone().addScaledVector(direction,-preferred.dot(direction)).normalize();return a.clone().addScaledVector(direction,along).addScaledVector(perpendicular,Math.sqrt(Math.max(0,upper*upper-along*along)));}
function rod(object,a,b,r){object.position.copy(a).lerp(b,.5);object.quaternion.setFromUnitVectors(UP,b.clone().sub(a).normalize());object.scale.set(r,a.distanceTo(b),r);}
function sphere(object,p,r){object.position.copy(p);object.quaternion.identity();object.scale.setScalar(r);}
function morph(part,name,value){part?.traverse(o=>{const i=o.morphTargetDictionary?.[name];if(i!==undefined)o.morphTargetInfluences[i]=value;});}
function alpha(part,value){part.visible=value>.002;part.traverse(o=>{if(!o.isMesh)return;for(const m of(Array.isArray(o.material)?o.material:[o.material])){m.opacity=value;m.depthWrite=value>.98;}o.castShadow=value>.45;});}

export function createWalker(asset,scene,camera,ui,prepareMaterial,onWish){
 const actors=[];
 asset.scene.traverse(root=>{const who=root.userData.rtActorRoot;if(!who)return;const parts={};root.traverse(o=>{const key=o.userData.rtPart;if(key&&!parts[key])parts[key]=o;});
  if(!parts.head||!parts.left_hand||!parts.right_shoe)throw new Error('Incomplete walking character '+who);
  root.traverse(o=>{if(!o.isMesh)return;const clone=m=>{const n=prepareMaterial(m.clone());n.transparent=true;return n;};o.material=Array.isArray(o.material)?o.material.map(clone):clone(o.material);o.castShadow=true;o.receiveShadow=true;});
  actors.push({who,side:who==='neria'?-1:1,root,parts,headPosition:new V()});
 });
 for(const a of actors){a.root.removeFromParent();a.root.position.set(0,0,0);a.root.quaternion.identity();a.root.scale.setScalar(1);a.root.visible=false;scene.add(a.root);}
 const w={mode:'film',z:START,lateral:0,floor:floorAt(0,START),progress:0,distance:0,speed:0,direction:1,elapsed:0,idle:0,hasMoved:false,auto:false,look:false,lookBlend:0,gaze:0,keys:new Set(),stick:{id:null,x:0,y:0},drag:{id:null,x:0,angle:0},yaw:0,yawTarget:0,enter:0,arrival:0,cameraStart:null,arrivalX:0,arrivalFloor:0,sinceStop:0,stopArmed:false,promptCount:0,promptUntil:0,stopText:'',speech:'',chimes:0,lastTrail:0,handGap:0,feet:[]};
 let captionKey=null,audio=null;const tones=new Set();
 function active(){return w.mode==='walk'&&ui.state.started;}
 function clearInput(){w.keys.clear();w.auto=false;w.stick.x=w.stick.y=0;for(const [part,element]of[[w.stick,$('walk-stick')],[w.drag,$('experience')]]){const id=part.id;part.id=null;if(id!==null&&element.hasPointerCapture(id))element.releasePointerCapture(id);}$('stick-knob').style.transform='';syncButton();}
 function syncButton(){$('walk-forward').setAttribute('aria-pressed',String(w.auto));$('walk-forward').innerHTML=w.auto?'Stay here a moment <span aria-hidden="true">Ⅱ</span>':'Walk with me <span aria-hidden="true">↑</span>';}
 function reset(mode){clearInput();Object.assign(w,{mode,z:START,lateral:0,floor:floorAt(center(START),START),progress:0,distance:0,speed:0,direction:1,elapsed:0,idle:0,hasMoved:false,look:false,lookBlend:0,gaze:0,yaw:0,yawTarget:0,enter:0,arrival:0,sinceStop:0,stopArmed:false,promptCount:0,promptUntil:0,stopText:'',speech:'',chimes:0,lastTrail:0});captionKey=null;$('look-at-him').setAttribute('aria-pressed','false');$('walk-hud').hidden=true;$('walk-speech').hidden=true;$('arrival-note').hidden=true;document.body.classList.remove('walking','walking-intro');}
 function start(){reset('intro');ui.state.mode='intro';ui.state.time=0;document.body.classList.add('walking-intro');}
 function preview(enabled){reset(enabled?'preview':'film');ui.state.time=enabled?20:0;}
 function stop(){reset('film');ui.state.mode='cinematic';}
 function unlockAudio(){try{const Context=window.AudioContext||window.webkitAudioContext;if(!Context)return;if(!audio)audio=new Context();if(audio.state==='suspended')audio.resume().catch(()=>{});}catch{}}
 function stopTones(){for(const o of tones){try{o.stop();}catch{}}tones.clear();}
 function chime(){if(!ui.isSoundOn()||ui.state.paused||document.hidden||audio?.state!=='running')return;const now=audio.currentTime;w.chimes++;for(const[i,hz]of[523.251,659.255,783.991,1046.502].entries()){const o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.value=hz;g.gain.setValueAtTime(0,now+i*.085);g.gain.linearRampToValueAtTime(.017/(1+i*.28),now+i*.085+.018);g.gain.exponentialRampToValueAtTime(.0001,now+1.5+i*.085);o.connect(g);g.connect(audio.destination);tones.add(o);o.onended=()=>{tones.delete(o);o.disconnect();g.disconnect();};o.start(now+i*.085);o.stop(now+1.6+i*.085);}}
 function advance(dt,state){
  if(w.mode==='film'||w.mode==='preview')return false;
  if(w.mode==='intro'){
   if(state.time<11)return false;w.mode='enter';state.mode='enter';w.enter=0;w.cameraStart={eye:camera.position.toArray(),at:cameraAt(state.time,innerWidth/innerHeight)[1]};document.body.classList.remove('walking-intro');document.body.classList.add('walking');captionKey=null;return true;
  }
  if(w.mode==='enter'){w.enter+=dt;state.time=mix(11,20,between(w.enter,0,2.2));if(w.enter>=2.2){w.mode='walk';state.mode='walk';$('walk-hud').hidden=false;captionKey=null;}return true;}
  if(w.mode==='arrival'){w.arrival+=dt;state.time=32+w.arrival*.5;w.distance+=dt*.42;w.lookBlend=mix(w.lookBlend,0,1-Math.exp(-dt*3));w.gaze=mix(w.gaze,0,1-Math.exp(-dt*3));
   if(w.arrival>=ARRIVAL){w.mode='film';state.mode='cinematic';document.body.classList.remove('walking');$('arrival-note').hidden=true;$('walk-speech').hidden=true;captionKey=null;}return true;
  }
  w.elapsed+=dt;
  let x=Number(w.keys.has('KeyD')||w.keys.has('ArrowRight'))-Number(w.keys.has('KeyA')||w.keys.has('ArrowLeft'))+w.stick.x;
  let f=Number(w.keys.has('KeyW')||w.keys.has('ArrowUp'))-Number(w.keys.has('KeyS')||w.keys.has('ArrowDown'))-w.stick.y;if(w.auto)f=1;
  const length=Math.hypot(x,f);if(length>1){x/=length;f/=length;}
  const oldZ=w.z,oldX=center(w.z)+w.lateral;w.z=clamp(w.z-f*dt*.82,END,START);w.lateral=clamp(w.lateral+x*dt*.26,-.12,.12);
  const moved=Math.hypot(w.z-oldZ,center(w.z)+w.lateral-oldX);w.speed=mix(w.speed,moved/Math.max(.001,dt),1-Math.exp(-dt*10));if(Math.abs(f)>.05)w.direction=Math.sign(f);
  w.floor=mix(w.floor,floorAt(center(w.z)+w.lateral,w.z),1-Math.exp(-dt*12));w.distance+=moved;w.sinceStop+=moved;if(w.sinceStop>.17)w.stopArmed=true;
  if(moved>.0001){w.idle=0;w.hasMoved=true;w.promptUntil=0;}else w.idle+=dt;
  w.progress=Math.max(w.progress,(START-w.z)/(START-END));state.time=20+w.progress*12;
  if(w.stopArmed&&w.idle>1.3){w.stopArmed=false;w.sinceStop=0;w.promptCount++;w.stopText=lines[(w.promptCount-1)%lines.length];w.promptUntil=w.elapsed+6.4;chime();onWish?.(center(w.z)+w.lateral,w.floor+1.04,w.z-.055,28);}
  w.gaze=mix(w.gaze,w.look||w.idle>.45?1:0,1-Math.exp(-dt*3.2));w.lookBlend=mix(w.lookBlend,w.look?1:0,1-Math.exp(-dt*2.7));w.yaw=mix(w.yaw,w.yawTarget,1-Math.exp(-dt*2.4));
  if(w.distance-w.lastTrail>.28){w.lastTrail=w.distance;onWish?.(center(w.z)+w.lateral,w.floor+.06,w.z+.10,5);}
  if(w.z<=END+.00001){w.cameraStart=cameraPose();w.arrivalX=center(w.z)+w.lateral;w.arrivalFloor=w.floor;clearInput();w.mode='arrival';state.mode='arrival';w.arrival=0;w.look=false;$('walk-hud').hidden=true;$('walk-speech').hidden=true;$('arrival-note').hidden=false;captionKey=null;}
  return true;
 }
 function cameraPose(){
  if(w.mode==='film'||w.mode==='intro')return null;
  if(w.mode==='preview')return innerWidth/innerHeight<.85?{eye:[2.2,4.7,19.5],at:[.05,1.5,9],fov:46}:{eye:[4.5,4.7,16.9],at:[0,1.7,6.4],fov:46};
  const cx=center(w.z)+w.lateral,portrait=innerWidth/innerHeight<.85,distance=portrait?6.3:5.1;
  let eye=[cx+Math.sin(w.yaw)*distance,3.02, w.z+Math.cos(w.yaw)*distance],at=[cx,1.5,w.z-1.05];
  const close=[cx+(portrait?.65:.43),w.floor+1.74,w.z+(portrait?.65:.30)],closeAt=[cx-.30,w.floor+1.76,w.z-.025];eye=eye.map((v,i)=>mix(v,close[i],w.lookBlend));at=at.map((v,i)=>mix(v,closeAt[i],w.lookBlend));
  if(w.mode==='enter'){const t=between(w.enter,0,2.2);return{eye:w.cameraStart.eye.map((v,i)=>mix(v,eye[i],t)),at:w.cameraStart.at.map((v,i)=>mix(v,at[i],t)),fov:mix(42,46,t)};}
  if(w.mode==='arrival'){const end=cameraAt(ui.state.time,innerWidth/innerHeight),t=between(w.arrival,0,ARRIVAL);return{eye:w.cameraStart.eye.map((v,i)=>mix(v,end[0][i],t)),at:w.cameraStart.at.map((v,i)=>mix(v,end[1][i],t)),fov:mix(w.cameraStart.fov,42,t)};}
  return{eye,at,fov:mix(46,portrait?58:46,w.lookBlend)};
 }
 function handover(){return w.mode==='arrival'?between(w.arrival,5.65,ARRIVAL):w.mode==='film'?1:0;}
 function chairShift(){return ['preview','enter','walk'].includes(w.mode)?.38:w.mode==='arrival'?.38*(1-between(w.arrival,4.6,5.65)):0;}
 function poseActor(a,clock){
  const s=a.side,female=s===1,p=a.parts,arriving=w.mode==='arrival';let x=center(w.z)+w.lateral+s*.37,z=w.z,yaw=0,sit=0,floor=w.floor;
  if(arriving){const travel=between(w.arrival,0,3.7),out=1-Math.pow(1-travel,3),seat=between(w.arrival,3.75,4.65),slide=between(w.arrival,4.6,5.65);x=mix(w.arrivalX+s*.37,s*1.42,out)+s*.31*seat-s*.38*slide;z=mix(END,.65,travel);yaw=s*Math.PI/2*between(w.arrival,2.6,3.75);sit=seat;floor=mix(w.arrivalFloor,.245,between(w.arrival,0,1.5));}
  const moving=arriving?(1-sit):clamp(w.speed/.82),phase=w.distance/.70,bob=(ui.reduced.matches?0:.011*Math.sin(phase*Math.PI*4)*moving+.004*Math.sin(clock*1.5));
  const root=new V(x,floor,z),rotation=new Q().setFromAxisAngle(UP,yaw),world=(x,y,z)=>new V(x,y,z).applyQuaternion(rotation).add(root);
  const chest=mix(1.285-(female?.05:0),.91,sit)+bob,hip=mix(.94-(female?.05:0),.59,sit)+bob;
  const pose=(part,point,scale=[1,1,1])=>{part.position.copy(point);part.quaternion.copy(rotation);part.scale.fromArray(scale);};
  pose(p.torso,world(0,chest,0));pose(p.waist,world(0,(hip+chest-.07)*.5,.018*(1-sit)),[.163,chest-hip+.03,.127]);pose(p.hip,world(0,hip,-.05*sit));morph(p.hip,'Seated',sit);
  if(p.skirt){pose(p.skirt,world(0,hip,-.05*sit));morph(p.skirt,'Seated',sit);}
  const gaze=arriving?0:w.gaze,headYaw=yaw+s*(female?w.lookBlend:gaze)*1.40*(1-sit)+s*.16*sit;
  pose(p.head,world(0,chest+.5,.01));p.head.quaternion.setFromEuler(new THREE.Euler(-.015*gaze,headYaw,s*.025*gaze));a.headPosition.copy(p.head.position).add(new V(0,.15,0));
  const blink=Math.exp(-Math.pow(((clock+(female?2.3:.7))%4.8-2.4)/.065,2));morph(p.head,'Blink',ui.reduced.matches?0:blink*.95);morph(p.head,'Smile',mix(.35,.85,w.lookBlend)*(1-handover()));
  const hands=[];
  for(const [sign,label]of[[-1,'left'],[1,'right']]){
   const inner=sign===-s,shoulder=world(sign*.18,chest+.18,-.015),swing=Math.sin(phase*Math.PI*2)*.10*moving;
   const free=world(sign*.275,chest-.39,-.025-sign*swing),shared=new V(center(w.z)+w.lateral+s*.014,w.floor+1.04,w.z-.055);
   let wrist=inner?shared:free;
   if(arriving){const release=between(w.arrival,.1,1);wrist=inner?shared.lerp(free,release):free;wrist.lerp(world(sign*.19,.81,-.51),sit);}
   const elbow=bend(shoulder,wrist,.275,.265,new V(sign*.1,0,-.22).applyQuaternion(rotation));if(sit)elbow.lerp(world(sign*.25,.77,-.225),sit);
   rod(p[label+'_upper_arm'],shoulder,elbow,mix(female?.050:.057,.057,sit));rod(p[label+'_forearm'],elbow,wrist,mix(female?.039:.044,.044,sit));sphere(p[label+'_shoulder'],shoulder,female?.053:.062);sphere(p[label+'_elbow'],elbow,female?.050:.055);
   const hand=p[label+'_hand'];hand.position.copy(wrist).lerp(world(sign*.19,.805,-.55),sit);
   const handRotation=inner?new Q().setFromAxisAngle(new V(0,0,1),s*Math.PI/2):new Q().setFromEuler(new THREE.Euler(-Math.PI/2,sign*Math.PI/2,0,'YXZ'));
   handRotation.slerp(IDENTITY,sit);hand.quaternion.copy(rotation).multiply(handRotation);hand.scale.setScalar(1);morph(hand,'Open',sit);if(inner)hands.push(hand.position.clone());
   const cycle=(phase+(sign===1?0:.5))%1;let stride,lift;
   if(cycle<.6){stride=.21-cycle*.70;lift=0;}else{const u=(cycle-.6)/.4;stride=-.21+.42*u*u*(3-2*u);lift=.085*Math.sin(u*Math.PI);}
   stride*=moving*w.direction;lift*=moving;
   const hipPoint=world(sign*.115,hip-.025,-.02),standingAnkle=world(sign*.135,.09+lift,-stride-.035);
   const footCenter=standingAnkle.clone().add(new V(0,0,-.06).applyQuaternion(rotation)),toe=new V(0,0,-.10).applyQuaternion(rotation),heel=toe.clone().multiplyScalar(-.8);
   const support=Math.max(floorAt(footCenter.x,footCenter.z),floorAt(footCenter.x+toe.x,footCenter.z+toe.z),floorAt(footCenter.x+heel.x,footCenter.z+heel.z));
   standingAnkle.y+=support-floor;
   const ankle=standingAnkle.clone().lerp(world(sign*.13,.09,-.405),sit),knee=bend(hipPoint,ankle,female?.415:.445,female?.405:.425,FORWARD.clone().applyQuaternion(rotation));if(sit)knee.lerp(world(sign*.12,.455,-.36),sit);
   rod(p[label+'_thigh'],hipPoint,knee,mix(female?.065:.083,.083,sit));rod(p[label+'_shin'],knee,ankle,female?.043:.057);sphere(p[label+'_knee'],knee,female?.063:.079);
   const shoe=standingAnkle.clone().add(new V(0,-.04,-.06).applyQuaternion(rotation)).lerp(world(sign*.13,.05,-.45),sit);pose(p[label+'_shoe'],shoe,[.066,.05,.12]);w.feet.push({actor:a.who,side:sign,sole:shoe.y-.05,floor:floorAt(shoe.x,shoe.z),support:mix(support,.243,sit),lift:lift*(1-sit)});
  }
  a.innerHand=hands[0];a.position=[x,floor,z];a.sit=sit;
 }
 function update(){const visible=!['film','intro'].includes(w.mode),fade=(w.mode==='enter'?between(w.enter,.15,1.5):1)*(1-handover());w.feet=[];
  for(const a of actors){a.root.visible=visible&&fade>.002;if(!a.root.visible)continue;poseActor(a,ui.state.clock);for(const[part,node]of Object.entries(a.parts)){let self=1;if(a.side===1){if(part==='head')self=1-between(w.lookBlend,.5,.9);else if(/^(torso|waist|hip|skirt)$|_(shoulder|upper_arm)$/.test(part))self=1-between(w.lookBlend,.66,.96);}alpha(node,fade*self);}}
  if(actors.every(a=>a.innerHand))w.handGap=Math.max(0,actors[0].innerHand.distanceTo(actors[1].innerHand)-.044);
 }
 function drawCaption(state){
  if(w.mode==='film'||w.mode==='intro'||w.mode==='preview')return false;
  $('ending').hidden=true;
  if(w.mode==='arrival'||w.look){captionKey=null;$('caption').classList.remove('visible');return true;}
  const item=w.mode==='enter'?['hand','Take my hand.','Let’s go and find our little table.']:w.elapsed<7.5?['steps','Every step, together.','You lead the way. I’ll hold your hand.']:w.progress>.72?['table','I saved us a little table.','A whole garden. And my favourite person.']:w.progress>.30?['flowers','Of course there are flowers.','I know someone who really likes them.']:null;
  const key=item?.[0]||'';if(key!==captionKey){captionKey=key;$('caption').classList.remove('visible');if(item){$('caption-title').textContent=item[1];$('caption-subtitle').textContent=item[2];$('caption-kicker').textContent='';$('caption').dataset.style='walk';requestAnimationFrame(()=>$('caption').classList.add('visible'));}}
  $('walk-progress').style.transform=`scaleX(${w.progress})`;$('walk-direction').textContent=w.progress>.78?'Just a few more steps.':'Follow the little stone path.';return true;
 }
 function speech(){let text='';if(active()&&!ui.state.paused){if(w.look&&w.idle>.5)text='My favourite view.';else if(w.elapsed<w.promptUntil)text=w.stopText;else if(w.hasMoved&&w.idle>11&&w.idle<17)text='Shall we keep going, my love?';}
  if(text!==w.speech){w.speech=text;$('walk-speaker').textContent=ui.state.config.yourName||'Neria';$('walk-speech-text').textContent=text;}$('walk-speech').hidden=!text;if(!text)return;
  const p=actors.find(a=>a.side===-1).headPosition.clone().project(camera),close=w.lookBlend>.35,short=innerHeight<500;
  $('walk-speech').style.left=(short?innerWidth*.22:close?innerWidth*.5:clamp((p.x*.5+.5)*innerWidth,innerWidth<600?110:150,innerWidth-(innerWidth<600?110:150)))+'px';
  $('walk-speech').style.top=(short?innerHeight*.66:close?innerHeight-(innerWidth<700?165:100):clamp((.5-p.y*.5)*innerHeight-30,175,innerHeight*.70))+'px';
 }
 function toggleLook(){if(!active()||ui.state.paused)return;w.look=!w.look;$('look-at-him').setAttribute('aria-pressed',String(w.look));}
 const keys=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight']);
 document.addEventListener('keydown',e=>{if($('personalize').open||e.target.matches('input,textarea')||e.ctrlKey||e.altKey||e.metaKey||w.mode==='film')return;if(keys.has(e.code)){e.preventDefault();if(!active()||ui.state.paused)return;w.auto=false;w.keys.add(e.code);syncButton();}else if(e.code==='KeyE'&&!e.repeat){e.preventDefault();toggleLook();}});
 document.addEventListener('keyup',e=>w.keys.delete(e.code));window.addEventListener('blur',clearInput);document.addEventListener('visibilitychange',()=>{if(document.hidden){clearInput();stopTones();}});
 $('walk-forward').onclick=()=>{if(!active())return;if(ui.state.paused)ui.pause(false);w.auto=!w.auto;w.keys.clear();syncButton();};$('look-at-him').onclick=toggleLook;
 for(const id of['begin','again','walk-forward','look-at-him','sound','switch-experience'])$(id).addEventListener('click',unlockAudio);
 function moveStick(e){if(e.pointerId!==w.stick.id)return;const r=$('walk-stick').getBoundingClientRect(),x=(e.clientX-r.left-r.width/2)/36,y=(e.clientY-r.top-r.height/2)/36,len=Math.hypot(x,y),scale=len>1?1/len:1;w.stick.x=Math.abs(x)<.12?0:x*scale;w.stick.y=Math.abs(y)<.12?0:y*scale;$('stick-knob').style.transform=`translate(${x*scale*27}px,${y*scale*27}px)`;}
 $('walk-stick').addEventListener('pointerdown',e=>{if(!active()||ui.state.paused||w.stick.id!==null)return;e.preventDefault();w.auto=false;syncButton();w.stick.id=e.pointerId;$('walk-stick').setPointerCapture(e.pointerId);moveStick(e);});$('walk-stick').addEventListener('pointermove',moveStick);
 const releaseStick=e=>{if(e.pointerId!==w.stick.id)return;w.stick.id=null;w.stick.x=w.stick.y=0;$('stick-knob').style.transform='';if($('walk-stick').hasPointerCapture(e.pointerId))$('walk-stick').releasePointerCapture(e.pointerId);};for(const name of['pointerup','pointercancel','lostpointercapture'])$('walk-stick').addEventListener(name,releaseStick);
 $('experience').addEventListener('pointerdown',e=>{if(!active()||ui.state.paused||w.drag.id!==null||e.target.closest('button,dialog,#walk-stick'))return;w.drag={id:e.pointerId,x:e.clientX,angle:w.yawTarget};$('experience').setPointerCapture(e.pointerId);});window.addEventListener('pointermove',e=>{if(e.pointerId===w.drag.id)w.yawTarget=clamp(w.drag.angle-(e.clientX-w.drag.x)/innerWidth*.8,-.18,.18);});
 const releaseDrag=e=>{if(e.pointerId!==w.drag.id)return;w.drag.id=null;if($('experience').hasPointerCapture(e.pointerId))$('experience').releasePointerCapture(e.pointerId);};for(const name of['pointerup','pointercancel','lostpointercapture'])$('experience').addEventListener(name,releaseDrag);
 return {start,preview,stop,advance,update,drawCaption,speech,cameraPose,handover,chairShift,pause(){clearInput();stopTones();},sound(on){if(!on)stopTones();},snapshot:()=>({mode:w.mode,z:w.z,lateral:w.lateral,progress:w.progress,elapsed:w.elapsed,idle:w.idle,auto:w.auto,look:w.look,lookBlend:w.lookBlend,gaze:w.gaze,speech:w.speech,promptCount:w.promptCount,chimes:w.chimes,handGap:w.handGap,arrival:w.arrival,feet:w.feet,keys:[...w.keys],stick:{x:w.stick.x,y:w.stick.y},actors:actors.map(a=>({who:a.who,position:a.position,sit:a.sit})),parts:actors.map(a=>({who:a.who,count:Object.keys(a.parts).length}))}),testWalkTo(progress){reset('walk');document.body.classList.add('walking');$('walk-hud').hidden=false;ui.state.mode='walk';w.z=mix(START,END,clamp(progress));w.progress=clamp(progress);w.floor=floorAt(center(w.z),w.z);w.elapsed=3;ui.state.time=20+w.progress*12;}};
}
