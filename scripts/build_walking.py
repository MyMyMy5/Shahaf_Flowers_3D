"""Build a standalone walking edition without modifying the original film."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'walk-together'
html = (ROOT / 'somewhere-just-us.html').read_text(encoding='utf-8')


def replace(old, new):
    global html
    assert html.count(old) == 1, f'Expected one integration point: {old[:100]!r}'
    html = html.replace(old, new, 1)


replace('</style>', (OUT / 'src/walk.css').read_text(encoding='utf-8') + '\n</style>')
replace('  <div id="loading"', (OUT / 'src/controls.html').read_text(encoding='utf-8') + '\n  <div id="loading"')
replace('I MADE YOU A LITTLE SOMETHING', 'A LITTLE WORLD FOR THE TWO OF US')
replace('Hey,<br><em>beautiful.</em>', 'Take<br><em>my hand.</em>')
replace("<span>Open when you're ready</span>", '<span>Let’s walk together</span>')
replace('Gentle mode is on. Play to watch the animation.', 'Gentle mode is on. Move at your own pace.')
replace('started=false,paused=false,finished=false,story=0,', 'started=false,paused=false,finished=false,story=20,')
replace('buildButterflies();buildPathRoses()}', 'buildButterflies();buildPathRoses();buildWalkingPeople()}')
replace('const body=mesh(c.body),head=mesh(c.head);', 'const body=mesh(c.body),head=mesh(walkingHead(female));')
replace('function updateCamera(){', 'function updateCamera(){\n if(updateWalkCamera())return;')
replace('function updateCaption(){', 'function updateCaption(){\n if(updateWalkCaption())return;')
replace("const chapters=[\n {at:0,end:11,title:'a little love letter'},\n {at:11,end:22,title:'someone likes flowers'},\n {at:22,end:32,title:'a place for us'},", 'const chapters=[')
replace('// Same soundtrack as Shahaf_Flowers/assets/song.mp3, embedded for offline sharing.', (OUT / 'src/walk.js').read_text(encoding='utf-8') + '\n// Same soundtrack as Shahaf_Flowers/assets/song.mp3, embedded for offline sharing.')
replace("`${config.herName}, this is my kind of love letter.`:'This is my kind of love letter.'", "`${config.herName}, I made a little place for us.`:'I made a little place for us.'")
replace("document.title=config.herName?`For ${config.herName}`:'For you';", "document.title=config.herName?`Walk with me, ${config.herName}`:'Walk with me';")
replace("function startFilm(){resetEndingOrbit();started=true;story=0;", "function startFilm(){resetWalk();resetEndingOrbit();started=true;story=20;")
replace("function setPaused(value){paused=!!value;", "function setPaused(value){paused=!!value;if(paused)clearWalkInput();")
replace("link.download='somewhere-just-us.html'", "link.download='walk-together.html'")
replace("story=c.at+.15;finished=false;", "enterCinematic();story=c.at+.15;finished=false;")
replace("if(e.key==='ArrowRight'&&started)", "if(e.key==='ArrowRight'&&started&&walk.mode==='cinematic'&&!e.repeat)")
replace("if(e.key==='ArrowLeft'&&started)", "if(e.key==='ArrowLeft'&&started&&walk.mode==='cinematic'&&!e.repeat)")
replace('if(started&&!finished){story=Math.min(FILM_END,story+dt);if(story>=FILM_END)finished=true;}', "if(started&&!finished){if(walk.mode==='cinematic'){story=Math.min(FILM_END,story+dt);if(story>=FILM_END)finished=true;}else tickWalk(dt);}")
replace('updateCamera();updateWorld();if(started)updateCaption();renderWorld();drawAtmosphere();', 'updateCamera();updateWorld();updateWalkingPeople();if(started)updateCaption();renderWorld();drawAtmosphere();updateWalkSpeech();')
replace('story=clamp(Number(t),0,FILM_END);', 'enterCinematic();story=clamp(Number(t),32,FILM_END);')
replace('updateCamera();updateWorld();updateCaption();renderWorld();drawAtmosphere();', 'updateCamera();updateWorld();updateWalkingPeople();updateCaption();renderWorld();drawAtmosphere();updateWalkSpeech();')
replace('return{started,paused,finished,story,clock,frameCount,', 'return{walk:walkSnapshot(),started,paused,finished,story,clock,frameCount,')
replace(' return points;\n}', ' addWalkParticles(point);particleCount=points.length/10;\n return points;\n}')
replace('function syncSound(){const on=audioEnabled;', 'function syncSound(){if(!audioEnabled)stopWalkChime();const on=audioEnabled;')
replace('if(paused)clearWalkInput();', 'if(paused){clearWalkInput();stopWalkChime();}')
replace('uTextureOn,uTime,uBotanical;uniform sampler2D', 'uTextureOn,uTime,uBotanical,uShadow;uniform sampler2D')
replace('  vec3 n=normalize(vNormal);if(!gl_FrontFacing)n=-n;', '  if(uShadow>.5){float a=pow(max(0.,1.-length((vUV-.5)*2.)),2.);gl_FragColor=vec4(.018,.012,.025,uAlpha*a);return;}\n  vec3 n=normalize(vNormal);if(!gl_FrontFacing)n=-n;')
replace('gl.uniform1f(mainProgram.u.uWind,m.wind);', 'gl.uniform1f(mainProgram.u.uWind,m.wind);gl.uniform1f(mainProgram.u.uShadow,m.shadow?1:0);gl.depthMask(!m.shadow);')
replace('gl.drawArrays(gl.TRIANGLES,0,m.count)}gl.disable(gl.BLEND);', 'gl.drawArrays(gl.TRIANGLES,0,m.count)}gl.depthMask(true);gl.disable(gl.BLEND);')
replace('crescent*(.1+.9*uNight);', 'crescent*smoothstep(.22,.84,uNight);')
replace("try{initRenderer();resize();resizeFX();buildWorld();", "if(testMode){window.__ONLY_US__.walkTo=progress=>{if(!started)startFilm();resetWalk();started=true;walk.z=mix(WALK_START,WALK_END,clamp(progress));walk.maxProgress=clamp(progress);story=20+12*walk.maxProgress;walk.elapsed=3;walk.hasMoved=progress>0;dirty=true;return walkSnapshot();};}\ntry{initRenderer();resize();resizeFX();buildWorld();")

(OUT / 'index.html').write_text(html, encoding='utf-8')
script = re.findall(r'<script>([\s\S]*?)</script>', html)[0]
(ROOT / 'output' / 'walking-syntax.js').write_text(script, encoding='utf-8')
print(f'Built {OUT / "index.html"} ({len(html):,} characters)')
