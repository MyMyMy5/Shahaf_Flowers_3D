import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
import {createPresentation} from './presentation.js';
import {cameraAt,between,mix,clamp,ORBIT,END} from './story.js';
import {createWalker} from './walking.js';

const $=id=>document.getElementById(id),scene=new THREE.Scene();
const params=new URLSearchParams(location.search),inspect=params.has('inspect');
let walker=null,preferredMode=['walk','film'].includes(params.get('mode'))?params.get('mode'):null,dirty=true;
const orbit={angle:0,target:0,id:null,startX:0,startTarget:0};let manualCamera=inspect;
function resetOrbit(){orbit.angle=orbit.target=0;releaseOrbit();manualCamera=inspect;dirty=true;}
const ui=createPresentation({onStart(){resetOrbit();if(preferredMode==='walk')walker?.start();else walker?.stop();},onSeek(){resetOrbit();walker?.stop();},onPause(paused){dirty=true;releaseOrbit();if(paused)walker?.pause();},onNamesChanged(){dirty=true;},onVisibility(visible){dirty=true;if(!visible){releaseOrbit();walker?.pause();}},onSound:on=>walker?.sound(on),advance:(dt,state)=>walker?.advance(dt,state)||false,drawCaption:state=>walker?.drawCaption(state)||false});
preferredMode=preferredMode||ui.state.config.preferredMode;
window.addEventListener('error',e=>ui.error(e.error||e.message));
scene.background=new THREE.Color('#111d34');scene.fog=new THREE.FogExp2('#15223a',.017);
const camera=new THREE.PerspectiveCamera(42,innerWidth/innerHeight,.1,150);
const renderer=new THREE.WebGLRenderer({canvas:$('world'),antialias:true,alpha:false,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,innerWidth<700?1.4:1.5));renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.AgXToneMapping;renderer.toneMappingExposure=1.10;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.VSMShadowMap;renderer.transmissionResolutionScale=.5;renderer.info.autoReset=false;
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.055;controls.enablePan=false;controls.minDistance=6;controls.maxDistance=29;controls.maxPolarAngle=Math.PI*.49;
controls.enabled=inspect;if(inspect)document.body.classList.add('inspect');
controls.target.set(-1.2,3.2,-.8);camera.position.set(7.5,6.9,17.3);
if(innerWidth/innerHeight<1)camera.position.sub(controls.target).multiplyScalar(1.5).add(controls.target);
controls.update();
RectAreaLightUniformsLib.init();
const pmrem=new THREE.PMREMGenerator(renderer),environment=new RoomEnvironment();
scene.environment=pmrem.fromScene(environment,.045).texture;scene.environmentIntensity=.10;environment.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight('#bbcffa','#263127',.21));
function directional(color,intensity,position,shadow=false){const light=new THREE.DirectionalLight(color,intensity);light.position.fromArray(position);light.castShadow=shadow;
 if(shadow){const size=innerWidth<700?1024:2048;light.shadow.mapSize.set(size,size);Object.assign(light.shadow.camera,{left:-16,right:16,top:16,bottom:-16,near:.1,far:45});light.shadow.bias=-.00015;light.shadow.normalBias=.012;light.shadow.radius=3;light.shadow.blurSamples=8;}
 scene.add(light);return light;}
const moonLight=directional('#bccaff',2.4,[4,15,2],true);directional('#ffdabc',.50,[0,8,8]);directional('#abb9ff',1.3,[-8,10,-6]);
const cafeLights=[];
function area(color,intensity,width,height,position,target){const l=new THREE.RectAreaLight(color,intensity,width,height);l.position.fromArray(position);l.lookAt(...target);l.userData.baseIntensity=intensity;scene.add(l);cafeLights.push(l);}
area('#ffc785',8,2.6,1.3,[0,4.2,-1.0],[0,1.0,.65]);
for(const x of[-2.1,2.1])area('#ffc38b',9,1.3,1.3,[x,3.2,-5.2],[x,1.7,-2.0]);
const target=new THREE.WebGLRenderTarget(innerWidth*renderer.getPixelRatio(),innerHeight*renderer.getPixelRatio(),{type:THREE.HalfFloatType});target.samples=Math.min(innerWidth<700?2:4,renderer.capabilities.maxSamples);
const composer=new EffectComposer(renderer,target);composer.addPass(new RenderPass(scene,camera));
class FocusPass extends BokehPass{render(renderer,...args){const auto=renderer.shadowMap.autoUpdate,background=this.scene.background,override=this.scene.overrideMaterial;renderer.shadowMap.autoUpdate=false;this.scene.background=null;try{super.render(renderer,...args);}finally{renderer.shadowMap.autoUpdate=auto;this.scene.background=background;this.scene.overrideMaterial=override;}}}
const focusPass=new FocusPass(scene,camera,{focus:7,aperture:.0015,maxblur:.004});focusPass.enabled=false;composer.addPass(focusPass);
const bloom=new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),.30,.45,1.15);composer.addPass(bloom);composer.addPass(new OutputPass());
composer.setSize(innerWidth,innerHeight);
const state={loaded:false,sourceMeshes:0,mergedMeshes:0,flowerDraws:0,flowers:0,frames:0,errors:[],triangles:0,calls:0};
const instancedFlowers=[],dynamicRoots=[],families=new Map();const tmp=new THREE.Object3D();let manifest=null;
let wishes=[];
const tilt=new THREE.Quaternion(),tiltEuler=new THREE.Euler();
const openingGroundFade={value:1},skyObjects={};

const skyMaterial=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:{time:{value:0},warm:{value:0}},vertexShader:`varying vec3 direction;void main(){direction=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,fragmentShader:`precision highp float;varying vec3 direction;uniform float time,warm;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}float fbm(vec2 p){return .52*noise(p)+.26*noise(p*2.04)+.13*noise(p*4.1)+.065*noise(p*8.25);}
void main(){vec3 d=normalize(direction);vec2 p=vec2(atan(d.z,d.x),asin(d.y));float h=smoothstep(-.1,.7,d.y);vec3 col=mix(vec3(.003,.007,.018),vec3(.001,.002,.006),h);col=mix(col,mix(vec3(.025,.009,.013),vec3(.006,.003,.014),h),warm*.85);float mist=fbm(p*vec2(3.,5.)+vec2(time*.003,0.));float band=exp(-pow((p.y-.48-.13*sin(p.x*3.))*4.,2.));col+=vec3(.003,.002,.010)*mist*band;gl_FragColor=vec4(col,1.);}`});
const sky=new THREE.Mesh(new THREE.BoxGeometry(180,180,180),skyMaterial);sky.frustumCulled=false;sky.renderOrder=-10;scene.add(sky);
function glowTexture(){const canvas=document.createElement('canvas');canvas.width=canvas.height=64;const c=canvas.getContext('2d'),g=c.createRadialGradient(32,32,0,32,32,32);g.addColorStop(0,'#fff9e9');g.addColorStop(.12,'rgba(255,235,196,.96)');g.addColorStop(.35,'rgba(255,214,160,.23)');g.addColorStop(1,'rgba(255,207,161,0)');c.fillStyle=g;c.fillRect(0,0,64,64);return new THREE.CanvasTexture(canvas);}
const pointTexture=glowTexture();
function addStars(){
 const p=[],c=[];for(let i=0;i<1000;i++){const hash=n=>{const x=Math.sin(n*127.1)*43758.5453;return x-Math.floor(x);};const angle=hash(i+9)*Math.PI*2,y=.12+hash(i+84)*.82,r=Math.sqrt(1-y*y);p.push(Math.cos(angle)*r*65,y*65,Math.sin(angle)*r*65);c.push(1.5+hash(i)*.9,1.5,1.8);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setAttribute('color',new THREE.Float32BufferAttribute(c,3));scene.add(new THREE.Points(g,new THREE.PointsMaterial({map:pointTexture,size:.23,vertexColors:true,transparent:true,opacity:.85,depthWrite:false,fog:false,blending:THREE.AdditiveBlending})));
 const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const x=canvas.getContext('2d');x.fillStyle='#dce6ff';x.beginPath();x.arc(128,128,100,0,Math.PI*2);x.fill();x.globalCompositeOperation='destination-out';x.beginPath();x.arc(166,109,95,0,Math.PI*2);x.fill();
 const moon=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas),color:new THREE.Color(2,2.1,2.5),transparent:true,depthWrite:false}));moon.position.set(15,14,-42);moon.scale.set(2.6,2.6,1);scene.add(moon);skyObjects.moon=moon;
}
addStars();

function prepareMaterial(mat){
 if(mat.userData.gardenPrepared)return mat;mat.userData.gardenPrepared=true;
 if(mat.transmission>0){mat.transparent=true;mat.opacity=mat.name.includes('RoofGlass')?.25:.30;mat.transmission=0;mat.depthWrite=false;mat.roughness=.19;mat.metalness=.18;}
 if(mat.name.includes('Glow'))mat.emissiveIntensity=3.5;
 if(mat.name.includes('Web_petal')){mat.color.set(0xffffff);mat.roughness=.49;mat.side=THREE.DoubleSide;}
 if(mat.name.includes('Hair')){mat.roughness=.64;mat.clearcoat=.015;}
 if(mat.name==='SF3D_Moss')mat.color.multiplyScalar(.48);
 if(mat.name==='SF3D_Moss')mat.onBeforeCompile=shader=>{shader.uniforms.uOpeningFade=openingGroundFade;shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vGardenPosition;').replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvGardenPosition=worldPosition.xyz;');shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nuniform float uOpeningFade;varying vec3 vGardenPosition;').replace('#include <fog_fragment>','#include <fog_fragment>\ngl_FragColor.rgb=mix(gl_FragColor.rgb,vec3(.003,.007,.018),smoothstep(1.8,11.0,length(vGardenPosition.xz-vec2(-2.6,6.6)))*uOpeningFade);');};
 return mat;
}

function addFlowerInstances(root,manifest){
 for(const[kind,name]of Object.entries(manifest.prototypes)){
  const prototype=root.getObjectByName(name);if(!prototype)throw new Error('Missing flower prototype '+kind);
  const instances=manifest.flowers.filter(f=>f.kind===kind).sort((a,b)=>a.start-b.start).map(f=>({...f,q:new THREE.Quaternion().fromArray(f.quaternion)})),parts=[];prototype.traverse(o=>{if(o.isMesh)parts.push(o);});
  prototype.updateWorldMatrix(true,true);
  for(const part of parts){
   const geometry=part.geometry.clone();geometry.applyMatrix4(part.matrixWorld);
   const mat=prepareMaterial(part.material.clone()),petal=mat.name.includes('Web_petal');
   const mesh=new THREE.InstancedMesh(geometry,mat,instances.length);mesh.name='Flowers_'+kind+'_'+mat.name;
   const dummy=new THREE.Mesh(geometry,mat);if(dummy.morphTargetInfluences)dummy.morphTargetInfluences.fill(1);
   instances.forEach((f,i)=>{tmp.position.fromArray(f.position);tmp.quaternion.fromArray(f.quaternion);tmp.scale.fromArray(f.scale);tmp.updateMatrix();mesh.setMatrixAt(i,tmp.matrix);if(petal)mesh.setColorAt(i,new THREE.Color().fromArray(f.color));if(dummy.morphTargetInfluences)mesh.setMorphAt(i,dummy);});
   mesh.instanceMatrix.needsUpdate=true;if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;if(mesh.morphTexture)mesh.morphTexture.needsUpdate=true;
   // Occlusion is baked from the opened Blender petals. Thin double-sided
   // petals cast shadows but avoid unstable self-shadow comparisons.
   mesh.castShadow=true;mesh.receiveShadow=false;mesh.computeBoundingSphere();scene.add(mesh);instancedFlowers.push({mesh,instances,dummy,kind});state.flowerDraws++;
  }
  prototype.removeFromParent();
 }
 state.flowers=manifest.flowers.length;
}

function familyGroup(name){
 if(!families.has(name)){const group=new THREE.Group();group.name=name;group.userData.pivot=new THREE.Vector3().fromArray(manifest.pivots?.[name]||[0,0,0]);group.position.copy(group.userData.pivot);scene.add(group);families.set(name,group);}
 return families.get(name);
}
function extractDynamics(root){
 root.updateWorldMatrix(true,true);const roots=[];
 root.traverse(o=>{if(/^SF3D_(Butterfly_\d\d|Floating_paper_lantern_\d\d)$/.test(o.name))roots.push(o);});
 for(const object of roots){
  const matrix=object.matrixWorld.clone();object.removeFromParent();matrix.decompose(object.position,object.quaternion,object.scale);
  const kind=object.name.includes('Butterfly')?'butterfly':'lantern',index=Number(object.name.slice(-2)),wings=[];
  object.traverse(o=>{if(o.isMesh){prepareMaterial(o.material);o.castShadow=false;}if(o.name.includes('wing_hinge'))wings.push(o);});
  const basePosition=object.position.clone(),baseScale=object.scale.clone();if(kind==='butterfly')baseScale.setScalar(index>=3?.39:.52);
  dynamicRoots.push({object,kind,index,wings,basePosition,baseScale});scene.add(object);
 }
}
function mergeStatic(root){
 root.updateWorldMatrix(true,true);const groups=new Map(),loose=[];
 root.traverse(o=>{
  if(!o.isMesh)return;state.sourceMeshes++;
  const material=prepareMaterial(o.material);
  let family=o.userData.rtGroup||'';let p=o.parent;
  while(p&&p!==root){if(p.userData.rtGroup&&!family)family=p.userData.rtGroup;p=p.parent;}
  family=family||'ground';
  if(material.transparent){o.castShadow=false;o.receiveShadow=true;loose.push({object:o,family});return;}
  const key=family+'|'+material.uuid;
  const geometry=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();geometry.applyMatrix4(o.matrixWorld);const pivot=familyGroup(family).userData.pivot;geometry.translate(-pivot.x,-pivot.y,-pivot.z);
  for(const name of Object.keys(geometry.attributes))if(!['position','normal','uv'].includes(name))geometry.deleteAttribute(name);
  if(!geometry.attributes.uv)geometry.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(geometry.attributes.position.count*2),2));
  geometry.morphAttributes={};geometry.clearGroups();
  if(!groups.has(key))groups.set(key,{geometries:[],material,family});groups.get(key).geometries.push(geometry);
 });
 for(const {geometries,material,family}of groups.values()){
  const geometry=mergeGeometries(geometries);if(!geometry)throw new Error('Cannot batch '+family);
  const actor=family.startsWith('neria_')||family.startsWith('shahaf_'),m=actor?material.clone():material;if(actor)m.transparent=true;
  const mesh=new THREE.Mesh(geometry,m);mesh.name=family+'_'+material.name;mesh.castShadow=!['terrain','grass'].includes(family);mesh.receiveShadow=true;familyGroup(family).add(mesh);state.mergedMeshes++;
  for(const g of geometries)g.dispose();
 }
 for(const {object:o,family}of loose){const matrix=o.matrixWorld.clone();o.removeFromParent();matrix.decompose(o.position,o.quaternion,o.scale);const group=familyGroup(family);o.position.sub(group.userData.pivot);group.add(o);}
}

const MAX_POINTS=1100,pointGeometry=new THREE.BufferGeometry();
for(const [name,size]of[['position',3],['aColor',3],['aSize',1],['aAlpha',1],['aShape',1],['aRotation',1]])pointGeometry.setAttribute(name,new THREE.BufferAttribute(new Float32Array(MAX_POINTS*size),size).setUsage(THREE.DynamicDrawUsage));
const particleMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,uniforms:{map:{value:pointTexture},scale:{value:1}},vertexShader:`attribute vec3 aColor;attribute float aSize,aAlpha,aShape,aRotation;uniform float scale;varying vec3 vColor;varying float vAlpha,vShape,vRotation;void main(){vec4 p=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*p;gl_PointSize=clamp(aSize*scale/max(.1,-p.z),1.,aSize<.1?32.:72.);vColor=aColor;vAlpha=aAlpha;vShape=aShape;vRotation=aRotation;}`,fragmentShader:`uniform sampler2D map;varying vec3 vColor;varying float vAlpha,vShape,vRotation;void main(){vec2 q=gl_PointCoord-.5;float c=cos(vRotation),s=sin(vRotation);q=mat2(c,-s,s,c)*q;float a=texture2D(map,gl_PointCoord).a;if(vShape>1.5){q.x-=.12*sin(q.y*5.);a=1.-smoothstep(.80,1.,length(q/vec2(.27,.47)));}else if(vShape>.5){float star=max(exp(-abs(q.x)*65.-abs(q.y)*7.),exp(-abs(q.y)*65.-abs(q.x)*7.));a=max(a*.6,star);}gl_FragColor=vec4(vColor,a*vAlpha);}`});
const particles=new THREE.Points(pointGeometry,particleMaterial);particles.frustumCulled=false;scene.add(particles);
const seedLight=new THREE.PointLight('#ffd093',0,5,2);scene.add(seedLight);
const hash=n=>{const a=Math.sin(n*127.1+311.7)*43758.5453;return a-Math.floor(a);};
const revealTimes={terrain:[-2,2],grass:[7,15],path:[17,20],terrace:[22,25],conservatory:[22,28],table:[29,31],chairs:[30,31.65],chair_left:[30,31.65],chair_right:[30,31.65],climbing:[28,31],lamps:[27,29.5],neria_body:[31.2,32.8],neria_head:[31.2,32.8],shahaf_body:[31.65,33.25],shahaf_head:[31.65,33.25]};
function animateWorld(t,clock){
 if(!manifest)return;
 for(const[name,group]of families){const times=revealTimes[name]||[22,28],g=between(t,...times);group.visible=g>.002;group.position.copy(group.userData.pivot);group.rotation.set(0,0,0);
  if(name.endsWith('_head')||name.endsWith('_body')){
   const alpha=walker?.handover()??1;group.visible=group.visible&&alpha>.002;group.traverse(o=>{if(o.isMesh){o.material.opacity=alpha;o.material.depthWrite=alpha>.98;o.castShadow=alpha>.45;}});
   group.scale.setScalar(Math.max(.001,g));if(name.endsWith('_head')){const body=families.get(name.replace('_head','_body'))?.userData.pivot;if(body)group.position.copy(body).lerp(group.userData.pivot,g);if(!ui.reduced.matches){group.rotation.y=Math.sin(clock*.53+(name[0]==='n'?1:2))*.035*g;group.position.y+=Math.sin(clock*1.45)*.006*g;}}
  }else group.scale.set(mix(.96,1,g),Math.max(.001,g),mix(.96,1,g));
  if(name==='chair_left'||name==='chair_right')group.position.x+=(name==='chair_left'?-1:1)*(walker?.chairShift()||0);
 }
 for(const batch of instancedFlowers){let visible=false;
  batch.instances.forEach((f,i)=>{const g=between(t,f.start,f.start+3.3),b=between(t,f.start+2.2,f.start+5.5);visible=visible||g>.002;tmp.position.fromArray(f.position);tmp.quaternion.copy(f.q);if(!ui.reduced.matches){tiltEuler.set(Math.sin(clock*.78+i)*.009*g,0,Math.cos(clock*1.03+i)*.007*g);tmp.quaternion.multiply(tilt.setFromEuler(tiltEuler));}tmp.scale.set(f.scale[0]*mix(.82,1,g),f.scale[1]*Math.max(.001,g),f.scale[2]*mix(.82,1,g));tmp.updateMatrix();batch.mesh.setMatrixAt(i,tmp.matrix);if(batch.dummy.morphTargetInfluences){batch.dummy.morphTargetInfluences.fill(b);batch.mesh.setMorphAt(i,batch.dummy);}});
  batch.mesh.count=batch.instances.filter(f=>t>f.start+.015).length;batch.mesh.visible=visible&&batch.mesh.count>0;batch.mesh.instanceMatrix.needsUpdate=true;if(batch.mesh.morphTexture)batch.mesh.morphTexture.needsUpdate=true;
 }
 for(const d of dynamicRoots){const {object,index}=d;
  if(d.kind==='butterfly'){
   const opening=index>=3,fade=opening?(ui.reduced.matches?0:between(t,2+(index-3)*.35,3.5+(index-3)*.35)*(1-between(t,10.5,13.5))):between(t,7,11);
   object.visible=fade>.005;object.scale.copy(d.baseScale).multiplyScalar(Math.max(.001,fade));const phase=index*Math.PI*2/3+(opening?Math.PI/3:0),a=clock*(opening?.64:.48)+phase,garden=opening?0:between(t,16,27);
   object.position.set(mix(-2.6+Math.sin(a)*(opening?1.25:1.6),Math.sin(a*.6)*5.5,garden),opening?.5+between(t,1.2,4.5)*2.1+Math.sin(a*1.3)*.28:3.05+Math.sin(a*1.2)*.5,mix(6.6+Math.cos(a)*.9,.5+Math.cos(a)*2.9,garden));
   object.rotation.set(.12*Math.sin(a),.22*Math.sin(a*2),Math.sin(a*.8)*.14);d.wings.forEach((wing,j)=>{wing.rotation.y=(j?1:-1)*Math.sin(clock*10.5+phase)*.88;});
  }else{const g=between(t,84+(index%4)*.7,91+(index%4)*.7),age=(clock*(.36+hash(index)*.19)+index*1.13)%12,fade=g*between(age,0,1)*(1-between(age,10,12));object.visible=fade>.005;object.scale.copy(d.baseScale).multiplyScalar(Math.max(.001,fade));object.position.copy(d.basePosition);object.position.y=1.7+age*.9;object.position.x+=Math.sin(clock*.4+index)*.55;object.rotation.z=Math.sin(clock*.8+index)*.055;}
 }
 for(const light of cafeLights)light.intensity=light.userData.baseIntensity*between(t,27,30);
 const warm=between(t,9,21)*(1-between(t,32,48));moonLight.color.copy(new THREE.Color('#bccaff')).lerp(new THREE.Color('#ffe0cd'),warm);scene.fog.density=mix(.052,.017,between(t,7,22));
 skyMaterial.uniforms.warm.value=warm;
 openingGroundFade.value=1-between(t,8,17);skyObjects.moon.material.opacity=between(t,38,58);
 state.growingFlowers=manifest.flowers.filter(f=>t>=f.start).length;state.visibleRoses=manifest.flowers.filter(f=>f.kind==='rose'&&t>=f.start).length;
 updateParticles(t,clock);
}
function updateParticles(t,clock){
 let count=0;const limit=innerWidth<700?720:MAX_POINTS,attributes=pointGeometry.attributes;
 const emit=(x,y,z,size,color,alpha=1,shape=0,rotation=0)=>{if(count>=limit||alpha<.002)return;attributes.position.setXYZ(count,x,y,z);attributes.aColor.setXYZ(count,...color);attributes.aSize.setX(count,size);attributes.aAlpha.setX(count,alpha);attributes.aShape.setX(count,shape);attributes.aRotation.setX(count,rotation);count++;};
 const gold=[3.4,2.0,.72],pink=[2.1,.9,1.15];
 for(let i=0;i<manifest.fireflies.length;i++){const p=manifest.fireflies[i];emit(p[0]+Math.sin(clock*.6+i)*.14,p[1]+Math.sin(clock*.71+i)*.13,p[2]+Math.cos(clock*.47+i)*.10,.055+hash(i)*.045,gold,between(t,7,13)*(.20+.30*(.5+.5*Math.sin(clock+i))));}
 const seed=between(t,.15,1.8),seedY=mix(5.8,.04,seed),seedFade=between(t,0,.4)*(1-between(t,1.9,2.8));emit(-2.6,seedY,6.6,.24,gold,seedFade,1,clock*.25);seedLight.position.set(-2.6,seedY,6.6);seedLight.intensity=seedFade*1.6;
 if(!ui.reduced.matches){
  const helix=between(t,1.4,3.3)*(1-between(t,8.5,11));for(let j=0;j<72;j++){const u=j/71,a=u*Math.PI*4.4+clock*1.1,r=.27+.06*Math.sin(u*Math.PI);emit(-2.6+Math.cos(a)*r,.05+u*3.1*between(t,1.2,4.5),6.6+Math.sin(a)*r,j%9===0?.075:.041,gold,helix*.8,j%9===0?1:0,a);}
  manifest.flowers.forEach((f,i)=>{if(innerWidth<700&&i%2&&f.kind==='garden')return;const age=t-f.start;if(age<.5||age>9)return;const hero=f.kind==='hero',n=hero?72:5;
   for(let j=0;j<n;j++){const born=(hero?1.0:1.4)+j*(hero?.05:.20),elapsed=age-born,life=2.5+hash(i*37+j)*1.4;if(elapsed<=0||elapsed>=life)continue;const u=elapsed/life,a=j*2.399963+i,r=(.22+elapsed*.28)*f.scale[0],petal=j%9===0;
    emit(f.position[0]+Math.cos(a)*r,f.position[1]+(f.kind==='rose'?1.8:2.65)*f.scale[1]*between(t,f.start,f.start+3.3)+elapsed*.32-elapsed*elapsed*.025,f.position[2]+Math.sin(a)*r,(petal?.12:.065)*Math.max(.5,f.scale[0]),petal?pink:gold,Math.sin(u*Math.PI)*.8,petal?2:j%4===0?1:0,a+clock*.3);
   }
  });
  wishes=wishes.filter(p=>clock-p.at<p.life);for(const p of wishes){const age=clock-p.at,u=age/p.life;emit(p.x+Math.cos(p.angle)*age*p.speed,p.y+.35*age-.04*age*age,p.z+Math.sin(p.angle)*age*p.speed,p.shape===2?.11:.065,p.shape===2?pink:gold,Math.sin(Math.PI*u)*.8,p.shape,p.angle+age*.6);}
 }
 const portrait=innerWidth/innerHeight<1,heartScale=portrait?(innerHeight<740?.25:.35):1,heartY=portrait?(innerHeight<740?6.0:6.2):8.1;
 const heart=between(t,96,105);for(let i=0;i<164;i++){const u=i/164;if(u>heart)continue;const a=u*Math.PI*2;emit(Math.sin(a)**3*2*heartScale,heartY+(13*Math.cos(a)-5*Math.cos(2*a)-2*Math.cos(3*a)-Math.cos(4*a))*.135*heartScale,-1.6,portrait?.09:.13,[2.7,1.5,1.6],between(heart-u,0,.04)*(.82+.12*Math.sin(clock*1.5+i)),i%14===0?1:0,0);}
 pointGeometry.setDrawRange(0,count);for(const a of Object.values(attributes))a.needsUpdate=true;particleMaterial.uniforms.scale.value=innerHeight*renderer.getPixelRatio()*.5*camera.projectionMatrix.elements[5];state.particles=count;
}
function wishBurst(x,y,z,count){if(ui.reduced.matches)return;for(let i=0;i<count&&wishes.length<(innerWidth<700?70:130);i++){const h=hash(ui.state.clock*5+i*3.31);wishes.push({x,y,z,at:ui.state.clock,life:1.5+h*1.8,angle:h*Math.PI*2,speed:.13+hash(i+73)*.24,shape:i%5===0?2:i%3===0?1:0});}}
function chooseMode(mode){preferredMode=mode;ui.state.config.preferredMode=mode;$('choose-film').setAttribute('aria-pressed',String(mode==='film'));$('choose-walk').setAttribute('aria-pressed',String(mode==='walk'));
 dirty=true;
 $('switch-experience').textContent=mode==='walk'?'Watch the film':'Walk together';
 if(!ui.state.started){walker?.preview(mode==='walk');document.querySelector('#cover h1').innerHTML=mode==='walk'?'Take<br><em>my hand.</em>':'Hey,<br><em>beautiful.</em>';$('begin').querySelector('span').textContent=mode==='walk'?'Let’s walk together':"Open when you're ready";document.querySelector('#cover p').textContent=mode==='walk'?`${ui.state.config.herName||'Beautiful'}, watch it grow. Then lead the way.`:`${ui.state.config.herName||'Beautiful'}, this is my kind of love letter.`;}
}
$('choose-film').onclick=()=>chooseMode('film');$('choose-walk').onclick=()=>chooseMode('walk');
$('switch-experience').onclick=()=>{chooseMode(preferredMode==='walk'?'film':'walk');ui.start();};

async function init(){
 const packed=window.__GARDEN_PACKED__;
 const loader=()=>new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 const[asset,data,cast]=await Promise.all([loader().loadAsync(packed?.url||'./assets/garden.glb'),packed?Promise.resolve(packed.manifest):fetch('./assets/garden-scene.json').then(r=>{if(!r.ok)throw new Error('Garden manifest missing');return r.json();}),loader().loadAsync(packed?.castUrl||'./assets/walking-cast.glb')]);
 manifest=data;addFlowerInstances(asset.scene,manifest);extractDynamics(asset.scene);mergeStatic(asset.scene);
 walker=createWalker(cast,scene,camera,ui,prepareMaterial,wishBurst);chooseMode(preferredMode);
 state.loaded=true;dirty=true;ui.ready();if(inspect){ui.start();ui.state.time=ui.state.clock=112;ui.pause(true);manualCamera=true;}if(params.has('at')){ui.seek(Number(params.get('at')),true);}
}
init().catch(error=>{state.errors.push(String(error));ui.error(error);});
function resize(){dirty=true;camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);}
addEventListener('resize',resize);
function releaseOrbit(){const id=orbit.id;orbit.id=null;if(id!==null&&$('experience').hasPointerCapture(id))$('experience').releasePointerCapture(id);}
$('experience').addEventListener('pointerdown',e=>{if(ui.state.time<ORBIT||e.pointerType!=='touch'||e.target.closest('button,dialog')||$('personalize').open)return;orbit.id=e.pointerId;orbit.startX=e.clientX;orbit.startTarget=orbit.target;$('experience').setPointerCapture(e.pointerId);});
window.addEventListener('pointermove',e=>{if(ui.state.time<ORBIT||e.target.closest('button,dialog')||$('personalize').open)return;if(e.pointerType==='touch'){if(e.pointerId!==orbit.id)return;orbit.target=clamp(orbit.startTarget+(e.clientX-orbit.startX)/innerWidth*.36,-.18,.18);}else orbit.target=clamp(e.clientX/innerWidth*2-1,-1,1)*.18;});
for(const name of['pointerup','pointercancel','lostpointercapture'])$('experience').addEventListener(name,e=>{if(e.pointerId===orbit.id)releaseOrbit();});
let lastDraw=0,lastTime=0;
function frame(now=0){requestAnimationFrame(frame);const dt=lastTime?Math.min((now-lastTime)*.001,.1):0;lastTime=now;if(document.hidden)return;ui.tick(dt);const previousOrbit=orbit.angle;orbit.angle=mix(orbit.angle,orbit.target,1-Math.exp(-dt*4));if(Math.abs(orbit.angle-orbit.target)<.00001)orbit.angle=orbit.target;if(Math.abs(orbit.angle-previousOrbit)>.000001)dirty=true;if(!ui.state.paused)dirty=true;if((!dirty&&!manualCamera)||now-lastDraw<1000/(innerWidth<700?30:45))return;lastDraw=now;
 const t=ui.state.time,clock=ui.state.clock;
 const walkCamera=walker?.cameraPose();
 if(manualCamera)controls.update();else if(walkCamera){camera.position.fromArray(walkCamera.eye);camera.lookAt(...walkCamera.at);camera.fov=walkCamera.fov;camera.updateProjectionMatrix();}else{const [eye,at]=cameraAt(t,innerWidth/innerHeight);if(t>=ORBIT){const x=eye[0]-at[0],z=eye[2]-at[2],c=Math.cos(orbit.angle),s=Math.sin(orbit.angle);eye[0]=at[0]+x*c+z*s;eye[2]=at[2]+z*c-x*s;}camera.position.fromArray(eye);camera.lookAt(...at);camera.fov=42;camera.updateProjectionMatrix();}
 camera.updateMatrixWorld();skyMaterial.uniforms.time.value=clock;animateWorld(t,clock);walker?.update();ui.draw();walker?.speech();
 const walking=walker?.snapshot(),portraitFocus=between(walking?.lookBlend||0,.9,1),openingFocus=(ui.state.mode==='cinematic'||ui.state.mode==='intro')?1-between(t,11,16):0;
 focusPass.enabled=ui.state.started&&(portraitFocus>.002||openingFocus>.002)&&!manualCamera;
 if(focusPass.enabled){const point=portraitFocus>0?new THREE.Vector3(...walkCamera.at):new THREE.Vector3(-2.6,2.65,6.6);focusPass.uniforms.focus.value=camera.position.distanceTo(point)-(portraitFocus>0?.10:0);focusPass.uniforms.aperture.value=portraitFocus>0?.0026*portraitFocus:.0015*openingFocus;focusPass.uniforms.maxblur.value=innerWidth<700?.005:.006;}
 renderer.info.reset();composer.render();state.frames++;state.triangles=renderer.info.render.triangles;state.calls=renderer.info.render.calls;dirty=false;
}
frame();
function visibleTriangles(){let triangles=0;scene.traverseVisible(o=>{if(o.isMesh)triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);});return triangles;}
if(params.has('test'))window.__GARDEN__={state:()=>({...state,...ui.state,config:undefined,walking:walker?.snapshot(),orbit:orbit.angle,camera:camera.position.toArray(),focus:focusPass.enabled,modelTriangles:visibleTriangles(),glError:renderer.getContext().getError(),groups:[...families].map(([name,g])=>({name,visible:g.visible,scale:g.scale.y,position:g.position.toArray()})),renderer:renderer.info.render}),seek(t){ui.seek(t,true);ui.state.clock=t;return this.state();},walkTo(progress){if(!ui.state.started)ui.start();walker.testWalkTo(progress);manualCamera=false;dirty=true;return this.state();},play(){ui.pause(false);},pause(){ui.pause(true);},view(eye,target){manualCamera=true;camera.position.fromArray(eye);controls.target.fromArray(target);controls.update();},flowerShadows(enabled){for(const f of instancedFlowers)f.mesh.receiveShadow=enabled;dirty=true;}};
