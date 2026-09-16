// This module is inlined by scripts/build_walking.py into the original renderer's
// closure. All generated geometry and the soundtrack remain available offline.
const WALK_START=11.35,WALK_END=3.15,ARRIVAL_SECONDS=5.2;
const walk={mode:'cover',z:WALK_START,lateral:0,maxProgress:0,elapsed:0,distance:0,
  speed:0,phase:0,idle:0,hasMoved:false,look:false,gaze:0,auto:false,keys:new Set(),
  stick:{id:null,x:0,y:0},drag:{id:null,x:0,angle:0},yaw:0,yawTarget:0,
  arrival:0,arrivalCamera:null,arrivalX:0,promptUntil:0,nextPrompt:0,promptCount:0,
  stopArmed:false,stopText:'',sinceStop:0,lookBlend:0,wishes:[],lastTrail:0,chimes:0,
  speech:'',speechAnchor:[0,2,10],handGap:0,feet:[],avatarPositions:[]};
const walkers=[];
const walkCenter=z=>Math.sin(z*.27)*.45;
const walkActive=()=>started&&walk.mode==='walk';
const add3=(a,b)=>a.map((v,i)=>v+b[i]);
const lerp3=(a,b,t)=>a.map((v,i)=>mix(v,b[i],t));

function resetWalk(){
 clearWalkInput();Object.assign(walk,{mode:'walk',z:WALK_START,lateral:0,maxProgress:0,elapsed:0,distance:0,
 speed:0,phase:0,idle:0,hasMoved:false,look:false,gaze:0,yaw:0,yawTarget:0,arrival:0,
 arrivalCamera:null,promptUntil:0,nextPrompt:0,promptCount:0,speech:'',stopArmed:false,
 stopText:'',sinceStop:0,lookBlend:0,wishes:[],lastTrail:0,chimes:0});
 document.body.classList.add('walking');$('walk-hud').hidden=false;$('arrival-note').hidden=true;
 $('walk-speech').hidden=true;$('look-at-him').setAttribute('aria-pressed','false');
 captionKey=null;syncWalkButton();
}

function clearWalkInput(){
 walk.keys.clear();walk.auto=false;walk.stick.x=walk.stick.y=0;
 for(const [state,element] of[[walk.stick,$('walk-stick')],[walk.drag,$('experience')]]){
  const id=state.id;state.id=null;if(id!==null&&element.hasPointerCapture(id))element.releasePointerCapture(id);
 }
 $('stick-knob').style.transform='';syncWalkButton();
}

function syncWalkButton(){
 $('walk-forward').setAttribute('aria-pressed',String(walk.auto));
 $('walk-forward').innerHTML=walk.auto?'Stay here a moment <span aria-hidden="true">Ⅱ</span>':'Walk with me <span aria-hidden="true">↑</span>';
}

function enterCinematic(){
 clearWalkInput();walk.mode='cinematic';walk.look=false;walk.speech='';
 document.body.classList.remove('walking');$('walk-hud').hidden=true;$('arrival-note').hidden=true;$('walk-speech').hidden=true;
 $('transport').classList.remove('initially-hidden');captionKey=null;
}

function startArrival(){
 walk.arrivalCamera=[eye.slice(),at.slice()];walk.arrivalX=walkCenter(walk.z)+walk.lateral;
 pointer.x=pointer.y=pointer.tx=pointer.ty=0;
 clearWalkInput();walk.mode='arrival';walk.arrival=0;walk.look=false;walk.speech='';
 $('walk-hud').hidden=true;$('arrival-note').hidden=false;$('walk-speech').hidden=true;captionKey=null;
}

function tickWalk(dt){
 walk.elapsed+=dt;
 if(walk.mode==='arrival'){
  walk.arrival+=dt;story=32+Math.min(walk.arrival,ARRIVAL_SECONDS);
  walk.phase+=dt*6;walk.gaze=mix(walk.gaze,0,1-Math.exp(-dt*3));
  if(walk.arrival>=ARRIVAL_SECONDS)enterCinematic();return;
 }
 if(walk.mode!=='walk')return;
 let x=Number(walk.keys.has('KeyD')||walk.keys.has('ArrowRight'))-Number(walk.keys.has('KeyA')||walk.keys.has('ArrowLeft'))+walk.stick.x;
 let f=Number(walk.keys.has('KeyW')||walk.keys.has('ArrowUp'))-Number(walk.keys.has('KeyS')||walk.keys.has('ArrowDown'))-walk.stick.y;
 if(walk.auto)f=1;
 const inputLength=Math.hypot(x,f);if(inputLength>1){x/=inputLength;f/=inputLength;}
 const oldZ=walk.z,oldX=walkCenter(oldZ)+walk.lateral;
 walk.z=clamp(walk.z-f*dt*.86,WALK_END,WALK_START);
 walk.lateral=clamp(walk.lateral+x*dt*.32,-.19,.19);
 const traveled=Math.hypot(walk.z-oldZ,walkCenter(walk.z)+walk.lateral-oldX);
 walk.speed=mix(walk.speed,traveled/Math.max(dt,.001),1-Math.exp(-dt*10));
 walk.distance+=traveled;walk.phase+=traveled*9.2;walk.sinceStop+=traveled;
 if(walk.sinceStop>.17)walk.stopArmed=true;
 if(traveled>.0001){walk.idle=0;walk.hasMoved=true;walk.promptUntil=0;}
 else walk.idle+=dt;
 walk.maxProgress=Math.max(walk.maxProgress,(WALK_START-walk.z)/(WALK_START-WALK_END));
 story=20+12*walk.maxProgress;
 // A new message belongs to a new pause. Remaining still never loops prompts.
 if(walk.stopArmed&&walk.idle>1.3){
  walk.stopArmed=false;walk.sinceStop=0;walk.promptCount++;
  walk.stopText=stopLines[(walk.promptCount-1)%stopLines.length];
  walk.promptUntil=walk.elapsed+6.4;walk.nextPrompt=walk.elapsed+11;
  wishBurst(walkCenter(walk.z)+walk.lateral,groundY(0,walk.z)+1.10,walk.z-.05,28);
  playWalkChime();
 }
 const wantsGaze=walk.look||walk.idle>.45;
 walk.gaze=mix(walk.gaze,wantsGaze?1:0,1-Math.exp(-dt*3.2));
 walk.lookBlend=mix(walk.lookBlend,walk.look?1:0,1-Math.exp(-dt*2.7));
 const target=walk.yawTarget;
 walk.yaw=mix(walk.yaw,target,1-Math.exp(-dt*2.4));
 if(walk.distance-walk.lastTrail>.28){
  walk.lastTrail=walk.distance;wishBurst(walkCenter(walk.z)+walk.lateral,.12,walk.z+.1,5);
 }
 if(walk.z<=WALK_END+.00001)startArrival();
}

function primitive(geo,c){return mesh(new Builder().add(geo,M.identity(),c));}

function walkingHead(female){
 const b=new Builder(),skin=female?'#e4b196':'#d5a485',hair=female?'#493126':'#382b26';
 const ball=(x,y,z,sx,sy,sz,c,ry=0,rz=0)=>b.add(sphere(28,20),pose(x,y,z,sx,sy,sz,0,ry,rz),c);
 ball(0,0,.027,.160,.207,.146,skin);
 // The hair follows a continuous scalp, with a lower hem behind the ears.
 const cap=surface((u,v)=>{const a=u*TAU,front=Math.cos(a),edge=front>0?1.15+.16*Math.sin(a+.4):1.82,phi=v*edge;
  return[Math.sin(a)*Math.sin(phi)*.169,Math.cos(phi)*.220+.005,Math.cos(a)*Math.sin(phi)*.154+.020];
 },48,20);b.add(cap,M.identity(),hair);
 for(const s of[-1,1]){
  ball(s*.155,-.02,.012,.024,.044,.026,skin);
  ball(s*.063,.024,.161,.026,.016,.010,'#f7e8d9');
  ball(s*.062,.024,.170,.011,.012,.004,'#3b302b');
  ball(s*.060,.028,.174,.0037,.0037,.002,'#fff6e5');
  ball(s*.105,-.042,.140,.026,.012,.004,female?'#d49b90':'#c4937e');
  curveTube(b,t=>[s*(.036+.048*t),.061+.008*Math.sin(t*Math.PI),.157],female?.004:.006,hair,12);
  if(female){curveTube(b,t=>[s*(.04+.045*t),.032+.008*Math.sin(t*Math.PI),.17],.003,hair,12);
   ball(s*.171,-.048,.017,.010,.012,.009,'#d8b878');}
 }
 ball(0,-.011,.172,.016,.029,.024,skin);
 curveTube(b,t=>[-.036+.072*t,-.075-.008*Math.sin(t*Math.PI),.164],.0045,'#a46d68',18);
 curveTube(b,t=>[-.029+.058*t,-.081-.010*Math.sin(t*Math.PI),.163],.003,'#d39787',18);
 if(female){
  for(let j=0;j<8;j++){
   const a=Math.PI*.43+j/7*Math.PI*1.14,x=Math.sin(a)*.137,z=Math.cos(a)*.118;
   const strand=surface((u,v)=>{const phi=u*TAU,taper=.35+.65*Math.pow(Math.sin((.18+.82*v)*Math.PI),.32),wave=Math.sin(v*4+j*.8)*.015;
    return[x+wave+Math.cos(phi)*.044*taper,.064-v*(.44+.02*Math.cos(j)),z-.01-v*.065+Math.sin(phi)*.043*taper];
   },16,18);b.add(strand,M.identity(),hair);
  }
  ball(.073,.146,.089,.078,.055,.065,hair,0,.28);
  blossom(b,.168,.081,.055,.055,'#efb8c5',-.4);
 }else{
  for(let j=0;j<6;j++)ball(-.111+j*.042,.175+.011*Math.sin(j),.055,.046,.052,.068,hair,.1,-.26);
 }
 return b;
}

function buildWalkingPeople(){
 for(const female of[false,true]){
  const skin=female?'#e4b196':'#d5a485',suit=female?'#d7a0b2':'#3d5d55',pants='#303c3e';
  const torso=new Builder();
  torso.add(sphere(28,20),pose(0,0,0,.22,.285,.145),suit);
  torso.add(cylinder(.63,.82,20),pose(0,.275,.005,.087,.12,.085),skin);
  if(!female){
   for(const side of[-1,1])torso.round(side*.055,.20,.115,.074,.115,.023,'#d7d8bc',0,side*.29);
   for(let i=0;i<4;i++)torso.ball(0,.115-i*.072,.146,.011,.011,.008,'#bcba94');
  }else{
   torso.add(torus(.083,.008,Math.PI,20),pose(0,.259,.017,1,.7,1,.23,0,Math.PI),'#dabb79');
  }
  const hip=new Builder();hip.add(sphere(24,16),pose(0,0,0,.195,.135,.145),female?suit:pants);
  if(female){
   const skirt=surface((u,v)=>{const a=u*TAU,r=.185+.115*v+.01*Math.sin(a*12)*v;return[Math.cos(a)*r,.06-v*.47,Math.sin(a)*r]},40,10);
   hip.add(skirt,M.identity(),'#d59bab');
   const hem=surface((u,v)=>{const a=u*TAU,r=.300+.006*v+.01*Math.sin(a*12);return[Math.cos(a)*r,-.397-v*.022,Math.sin(a)*r]},40,2);
   hip.add(hem,M.identity(),'#e7b4be');
  }
  const shadow=mesh(new Builder().add(quad(),M.identity(),'#111019'),{shadow:true,alpha:.42});
  const avatar={female,s:female?1:-1,shadow,torso:mesh(torso),waist:primitive(cylinder(.97,1,24),suit),hip:mesh(hip),head:mesh(walkingHead(female)),arms:[],legs:[],all:[],headPosition:[0,0,0],handPosition:[0,0,0]};
  for(const side of[-1,1]){
   avatar.arms.push({side,shoulder:primitive(sphere(20,14),female?skin:suit),upper:primitive(cylinder(1,1,20),female?skin:suit),lower:primitive(cylinder(1,1,20),female?skin:suit),joint:primitive(sphere(20,14),female?skin:suit),hand:primitive(sphere(20,14),skin)});
   avatar.legs.push({side,upper:primitive(cylinder(1,1,12),female?skin:pants),lower:primitive(cylinder(1,1,12),female?skin:pants),joint:primitive(sphere(12,8),female?skin:pants),shoe:primitive(sphere(12,8),female?'#97695e':'#253334')});
  }
  avatar.all=[avatar.torso,avatar.waist,avatar.hip,avatar.head,...avatar.arms.flatMap(a=>[a.shoulder,a.upper,a.lower,a.joint,a.hand]),...avatar.legs.flatMap(a=>[a.upper,a.lower,a.joint,a.shoe])];
  walkers.push(avatar);
 }
}

// Two-bone IK chooses a bend in a preferred direction while maintaining the
// two bone lengths. Both inner arms solve toward the same handhold in world space.
function bendJoint(root,tip,upper,lower,preferred){
 const direction=V.norm(V.sub(tip,root)),distance=clamp(Math.hypot(...V.sub(tip,root)),.01,upper+lower-.001);
 const along=(upper*upper-lower*lower+distance*distance)/(2*distance);
 const height=Math.sqrt(Math.max(0,upper*upper-along*along));
 const projected=preferred.map((v,i)=>v-direction[i]*V.dot(preferred,direction));
 const bend=V.norm(projected);
 return root.map((v,i)=>v+direction[i]*along+bend[i]*height);
}

function setLimb(limb,a,j,b,r,lowerRadius=r){
 limb.upper.model=tubePose(a,j,r);limb.lower.model=tubePose(j,b,lowerRadius);
 limb.joint.model=pose(...j,r*1.02,r*1.02,r*1.02);
}

function arrivalPosition(avatar){
 const t=walk.arrival,s=avatar.s,travel=between(t,0,3.7);
 // Separate around the table's front edge before moving beside the chairs.
 const x=mix(walk.arrivalX+s*.37,s*1.44,ease(travel));
 const z=mix(WALK_END,.65,smooth(travel));
 const yaw=Math.PI+s*Math.PI/2*between(t,2.8,4.2);
 return{x,z,yaw,sit:between(t,3.75,4.95)};
}

function updateWalkingPeople(){
 const active=walk.mode!=='cinematic';
 let handover=walk.mode==='arrival'?between(walk.arrival,4.55,5.2):0;
 for(const person of people)if(active)person.body.alpha=person.head.alpha=handover;
 for(const avatar of walkers)for(const m of avatar.all)m.alpha=active?1-handover:0;
 for(const avatar of walkers)avatar.shadow.alpha=active?.42*(1-handover):0;
 if(!active)return;
 const center=walkCenter(walk.z)+walk.lateral,arrival=walk.mode==='arrival';
 const moving=arrival?1:clamp(walk.speed/.86),swing=Math.sin(walk.phase),breath=Math.sin(clock*1.6)*.004;
 const shared=[center,groundY(center,walk.z)+1.04+Math.sin(walk.phase*2)*.009*moving,walk.z-.055];
 const handPositions=[];walk.feet=[];walk.avatarPositions=[];
 for(const avatar of walkers){
  const female=avatar.female,s=avatar.s;
  const p=arrival?arrivalPosition(avatar):{x:center+s*.37,z:walk.z,yaw:Math.PI,sit:0};
  const floor=arrival?mix(groundY(walkCenter(p.z),p.z)+.034,.166,between(walk.arrival,0,1.5)):groundY(walkCenter(p.z),p.z)+.034;
  const bob=Math.cos(walk.phase*2)*.014*moving*(1-p.sit)+breath;
  const root=pose(p.x,floor,p.z,1,1,1,0,p.yaw);
  avatar.shadow.model=pose(p.x,floor+.003,p.z,.85,1.05,1,-Math.PI/2,p.yaw);
  const world=local=>M.point(root,local);
  const height=female?-.065:0;
  const hipY=mix(.94+height,.79-floor,p.sit)+bob;
  const chestY=mix(1.285+height,1.06-floor,p.sit)+bob;
  const headY=mix(1.78+height,1.55-floor,p.sit)+bob;
  avatar.torso.model=M.mul(root,pose(0,chestY,.01,1,1,1,0,0,.018*swing*moving*(1-p.sit)));
  avatar.hip.model=M.mul(root,pose(0,hipY,.02));
  avatar.waist.model=M.mul(root,pose(0,(hipY+chestY-.07)/2,.018,.163,chestY-hipY+.03,.127));
  const gaze=arrival?0:walk.gaze;
  const headYaw=s>0?1.40*walk.lookBlend:-1.40*gaze;
  avatar.head.model=M.mul(root,pose(0,headY,.04,1,1,1,-.02*gaze,headYaw,s*.025*gaze));
  // Looking at him moves into her viewpoint; her own head leaves the lens.
  if(female&&!arrival)avatar.head.alpha*=1-between(walk.lookBlend,.5,.9);
  avatar.headPosition=world([0,headY+.12,.04]);
  walk.avatarPositions.push({female,position:[p.x,floor,p.z],yaw:p.yaw,sit:p.sit});
  for(const arm of avatar.arms){
   const side=arm.side,inner=side===s;
   const shoulder=world([side*.18,chestY+.16,.015]);
   const shoulderRadius=female?.053:.068;arm.shoulder.model=pose(...shoulder,shoulderRadius,shoulderRadius,shoulderRadius);
   const freeHand=world([side*.275,chestY-.39,.025+side*swing*.12*moving]);
   const hand=inner&&!arrival?shared:freeHand;
   let target=hand;
   if(arrival){
    const release=between(walk.arrival,.1,1);
    const carried=[mix(walk.arrivalX,0,between(walk.arrival,0,1)),floor+1.04,p.z-.055];
    target=inner?lerp3(carried,freeHand,release):freeHand;
    target=lerp3(target,world([side*.18,1.37-floor,.53]),p.sit);
   }
   const bend=world([side*.1,0,.22]).map((v,i)=>v-root[12+i]);
   const elbow=bendJoint(shoulder,target,.275,.265,bend);
   setLimb(arm,shoulder,elbow,target,female?.050:.065,female?.039:.050);
   arm.hand.model=M.mul(pose(...target,.047,.054,.035),M.ry(p.yaw));
   if(inner){avatar.handPosition=target;handPositions.push(target);}
  }
  for(const leg of avatar.legs){
   const side=leg.side,phase=walk.phase+(side===1?Math.PI:0);
   const stride=Math.sin(phase)*.22*moving*(1-p.sit),lift=Math.max(0,Math.cos(phase))*.080*moving*(1-p.sit);
   let hip=[side*.115,hipY-.025,.02],ankle=[side*.135,.060+lift,stride+.035];
   const sittingAnkle=[side*.14,.27-floor,.42];ankle=lerp3(ankle,sittingAnkle,p.sit);
   const a=world(hip),b=world(ankle),preferred=V.sub(world([0,0,1]),world([0,0,0]));
   const joint=bendJoint(a,b,.445,.435,preferred);
   setLimb(leg,a,joint,b,female?.065:.083,female?.043:.058);
   const foot=world([ankle[0],ankle[1]-.018,ankle[2]+.060]);
   leg.shoe.model=M.mul(pose(...foot,.062,.043,.126),M.ry(p.yaw));
   walk.feet.push({female,side,position:foot,floor});
  }
  if(!female)walk.speechAnchor=avatar.headPosition.slice();
 }
 walk.handGap=handPositions.length===2?Math.hypot(...V.sub(...handPositions)):0;
}

function walkCamera(){
 const cx=walkCenter(walk.z)+walk.lateral;
 const target=[cx,1.5,walk.z-1.05];
 const portrait=W/H<.85;
 const distance=portrait?6.3:5.1;
 const angle=walk.yaw;
 const camera=[cx+Math.sin(angle)*distance,3.02+Math.abs(angle)*.18,walk.z+Math.cos(angle)*distance];
 const floor=groundY(walkCenter(walk.z),walk.z)+.034;
 const intimate=[cx+(portrait?1.00:.72),floor+1.83,walk.z+(portrait?.70:.57)],intimateAt=[cx-.37,floor+1.69,walk.z-.03];
 return[lerp3(camera,intimate,walk.lookBlend),lerp3(target,intimateAt,walk.lookBlend)];
}

function updateWalkCamera(){
 if(walk.mode==='cinematic')return false;
 if(walk.mode==='cover'){
  eye=[4.5,4.7,16.9];at=[0,1.7,6.4];
 }else if(walk.mode==='arrival'){
  const finish=cameraAt(story),t=between(walk.arrival,0,ARRIVAL_SECONDS);
  if(W/H<1){const narrow=smooth((1.05-W/H)/.60),factor=mix(1,mix(1.62,1.38,between(story,47,58)),narrow)*mix(.86,1,between(story,11,26));finish[0]=finish[1].map((v,i)=>v+(finish[0][i]-v)*factor);}
  eye=lerp3(walk.arrivalCamera[0],finish[0],t);at=lerp3(walk.arrivalCamera[1],finish[1],t);
 }else{
  const [e,a]=walkCamera(),blend=between(walk.elapsed,0,1.8);
  eye=lerp3([4.5,4.7,16.9],e,blend);at=lerp3([0,1.7,6.4],a,blend);
 }
 const fov=walk.mode==='arrival'?mix(46,42,between(walk.arrival,0,ARRIVAL_SECONDS)):46;
 vp=M.mul(M.perspective(fov*Math.PI/180,W/H,.1,100),M.lookAt(eye,at));
 warmth=between(story,9,20)*(1-between(story,35,48));night=between(story,37,50);return true;
}

function updateWalkCaption(){
 if(walk.mode==='cinematic')return false;
 $('ending').hidden=true;$('experience').classList.remove('orbit-enabled');
 if(walk.mode==='arrival'){$('caption').classList.remove('visible');return true;}
 if(walk.look){captionKey=null;$('caption').classList.remove('visible');return true;}
 const progress=walk.maxProgress;
 let text=null;
 if(walk.elapsed<7.5)text={key:'hand',title:'Every step, together.',sub:'You lead the way. I’ll hold your hand.'};
 else if(progress>.72)text={key:'near',title:'I saved us a little table.',sub:'A whole garden. And my favourite person.'};
 else if(progress>.30)text={key:'flowers',title:'Of course there are flowers.',sub:'I know someone who really likes them.'};
 const key=text?text.key:'';
 if(key!==captionKey){
  captionKey=key;$('caption').classList.remove('visible');
  if(text){$('caption-title').textContent=text.title;$('caption-subtitle').textContent=text.sub;$('caption-kicker').textContent='';$('caption').dataset.style='walk';requestAnimationFrame(()=>$('caption').classList.add('visible'));}
 }
 $('walk-progress').style.transform=`scaleX(${progress})`;
 $('walk-direction').textContent=progress>.78?'Just a few more steps.':'Follow the little stone path.';
 return true;
}

function updateWalkSpeech(){
 let speech='';
 if(walkActive()&&!paused){
  if(walk.look&&walk.idle>.5)speech='My favourite view.';
  else if(walk.elapsed<walk.promptUntil)speech=walk.stopText;
  else if(walk.hasMoved&&walk.idle>11&&walk.idle<17)speech='Shall we keep going, my love?';
 }
 const changed=speech!==walk.speech;walk.speech=speech;
 $('walk-speech').hidden=!speech;if(!speech)return;
 if(changed){$('walk-speaker').textContent=config.yourName||'Neria';$('walk-speech-text').textContent=speech;}
 const p=M.point(vp,walk.speechAnchor);
 const intimate=walk.lookBlend>.35;
 const x=intimate?W*.5:clamp((p[0]*.5+.5)*W,W<600?110:150,W-(W<600?110:150));
 const y=intimate?H-(W<700?165:100):clamp((.5-p[1]*.5)*H-30,175,H*.70);
 $('walk-speech').style.left=x+'px';$('walk-speech').style.top=y+'px';
}

function walkSnapshot(){return{mode:walk.mode,z:walk.z,lateral:walk.lateral,progress:walk.maxProgress,elapsed:walk.elapsed,speed:walk.speed,auto:walk.auto,look:walk.look,gaze:walk.gaze,idle:walk.idle,promptCount:walk.promptCount,speech:walk.speech,handGap:walk.handGap,arrival:walk.arrival,yaw:walk.yaw,avatars:walk.avatarPositions,feet:walk.feet,keys:[...walk.keys],stick:{x:walk.stick.x,y:walk.stick.y},chimes:walk.chimes,audioState:walkAudio?.state||'not-started',wishes:walk.wishes.length};}

const walkKeys=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight']);
document.addEventListener('keydown',e=>{
 if(!walkActive()||$('personalize').open||e.target.matches('input,textarea'))return;
 if(walkKeys.has(e.code)){
  e.preventDefault();e.stopImmediatePropagation();if(paused)return;
  walk.auto=false;walk.keys.add(e.code);syncWalkButton();
 }else if(e.code==='KeyE'&&!e.repeat){e.preventDefault();toggleWalkLook();}
});
document.addEventListener('keyup',e=>{walk.keys.delete(e.code);});
window.addEventListener('blur',clearWalkInput);
document.addEventListener('visibilitychange',()=>{if(document.hidden)clearWalkInput();});
function toggleWalkLook(){if(!walkActive()||paused)return;walk.look=!walk.look;$('look-at-him').setAttribute('aria-pressed',String(walk.look));dirty=true;}
$('look-at-him').addEventListener('click',toggleWalkLook);
$('walk-forward').addEventListener('click',()=>{if(!walkActive())return;if(paused)setPaused(false);walk.auto=!walk.auto;walk.keys.clear();syncWalkButton();});

$('walk-stick').addEventListener('pointerdown',e=>{
 if(!walkActive()||paused||walk.stick.id!==null)return;
 e.preventDefault();walk.auto=false;syncWalkButton();walk.stick.id=e.pointerId;$('walk-stick').setPointerCapture(e.pointerId);moveWalkStick(e);
});
function moveWalkStick(e){
 if(e.pointerId!==walk.stick.id)return;
 const r=$('walk-stick').getBoundingClientRect(),x=(e.clientX-r.left-r.width/2)/36,y=(e.clientY-r.top-r.height/2)/36,len=Math.hypot(x,y),scale=len>1?1/len:1;
 walk.stick.x=Math.abs(x)<.12?0:x*scale;walk.stick.y=Math.abs(y)<.12?0:y*scale;
 $('stick-knob').style.transform=`translate(${x*scale*27}px,${y*scale*27}px)`;
}
$('walk-stick').addEventListener('pointermove',moveWalkStick);
function releaseWalkStick(e){
 if(e.pointerId!==walk.stick.id)return;walk.stick.id=null;walk.stick.x=walk.stick.y=0;$('stick-knob').style.transform='';
 if($('walk-stick').hasPointerCapture(e.pointerId))$('walk-stick').releasePointerCapture(e.pointerId);
}
for(const event of['pointerup','pointercancel','lostpointercapture'])$('walk-stick').addEventListener(event,releaseWalkStick);
$('experience').addEventListener('pointerdown',e=>{
 if(!walkActive()||paused||walk.drag.id!==null||e.target.closest('button,dialog,#walk-stick'))return;
 walk.drag={id:e.pointerId,x:e.clientX,angle:walk.yawTarget};$('experience').setPointerCapture(e.pointerId);
});
window.addEventListener('pointermove',e=>{
 if(e.pointerId!==walk.drag.id)return;
 walk.yawTarget=clamp(walk.drag.angle-(e.clientX-walk.drag.x)/W*.8,-.18,.18);dirty=true;
});
function releaseWalkDrag(e){if(e.pointerId!==walk.drag.id)return;walk.drag.id=null;if($('experience').hasPointerCapture(e.pointerId))$('experience').releasePointerCapture(e.pointerId);}
for(const event of['pointerup','pointercancel','lostpointercapture'])$('experience').addEventListener(event,releaseWalkDrag);

const stopLines=[
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
let walkAudio=null;const walkTones=new Set();
function unlockWalkAudio(){
 try{const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;
  if(!walkAudio)walkAudio=new Audio();if(walkAudio.state==='suspended')walkAudio.resume().catch(()=>{});
 }catch{}
}
function stopWalkChime(){for(const tone of walkTones){try{tone.stop();}catch{}}walkTones.clear();}
function playWalkChime(){
 if(!audioEnabled||paused||!visible||walkAudio?.state!=='running')return;
 const now=walkAudio.currentTime;walk.chimes++;
 for(const [i,hz]of[523.251,659.255,783.991,1046.502].entries()){
  const oscillator=walkAudio.createOscillator(),gain=walkAudio.createGain();
  oscillator.type='sine';oscillator.frequency.value=hz;
  gain.gain.setValueAtTime(0,now+i*.085);gain.gain.linearRampToValueAtTime(.017/(1+i*.28),now+i*.085+.018);
  gain.gain.exponentialRampToValueAtTime(.0001,now+1.5+i*.085);
  oscillator.connect(gain);gain.connect(walkAudio.destination);walkTones.add(oscillator);
  oscillator.onended=()=>{walkTones.delete(oscillator);oscillator.disconnect();gain.disconnect();};
  oscillator.start(now+i*.085);oscillator.stop(now+1.6+i*.085);
 }
}
for(const id of['begin','again','walk-forward','look-at-him','sound'])$(id).addEventListener('click',unlockWalkAudio);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopWalkChime();});
function wishBurst(x,y,z,count){
 if(reduced.matches)return;
 const cap=W<700?70:130;
 for(let i=0;i<count&&walk.wishes.length<cap;i++){
  const n=walk.distance*187+i*3.31+walk.promptCount*97,a=bloomHash(n)*TAU;
  walk.wishes.push({x,y,z,at:clock,a,v:.13+bloomHash(n+2)*.24,life:1.5+bloomHash(n+4)*1.8,shape:i%5===0?2:i%3===0?1:0});
 }
}
function addWalkParticles(point){
 if(reduced.matches)return;
 walk.wishes=walk.wishes.filter(p=>clock-p.at<p.life);
 for(const p of walk.wishes){const age=clock-p.at,t=age/p.life;
  point(p.x+Math.cos(p.a)*age*p.v,p.y+.35*age-.04*age*age,p.z+Math.sin(p.a)*age*p.v,p.shape===2?16:9,[1,.74,.48],Math.sin(Math.PI*t)*.74,p.shape,p.a+age*.6);
 }
}
