import {build} from 'esbuild';
import {readFile,writeFile} from 'node:fs/promises';
await build({entryPoints:['src/main.js'],bundle:true,format:'esm',target:'es2022',outfile:'app.js',minify:true,sourcemap:'external'});
const film=await readFile('../somewhere-just-us.html','utf8');
const start=film.lastIndexOf('<script>'),end=film.indexOf('</script>',start)+9;
if(start<0||end<start)throw new Error('Cannot find the original film script');
const extra=await readFile('src/garden.css','utf8');
const template=film.slice(0,start)+'GARDEN_SCRIPT'+film.slice(end);
const walkCSS=await readFile('../walk-together/src/walk.css','utf8'),walkControls=await readFile('../walk-together/src/controls.html','utf8');
const choice='<div id="mode-choice" role="group" aria-label="Choose your experience"><button id="choose-film" type="button" aria-pressed="true">Watch our little film</button><button id="choose-walk" type="button" aria-pressed="false">Walk together</button></div>';
const html=template.replace('</style>',walkCSS+'\n'+extra+'\n</style>').replace('    <p id="reduced-note"',choice+'\n    <p id="reduced-note"').replace('  <div id="loading"',walkControls+'\n  <div id="loading"').replace('<p id="orbit-hint"','<button id="switch-experience" class="text-button">Walk together</button><p id="orbit-hint"');
const online=html.replace(/(<audio id="music" src=")data:audio\/mpeg;base64,[^"]+/, '$1../assets/song.mp3');
await writeFile('index.html',online.replace('GARDEN_SCRIPT','<script type="module" src="app.js"></script>'));
const app=(await readFile('app.js','utf8')).replace(/<\/script/gi,'<\\/script');
const packed={url:'data:model/gltf-binary;base64,'+(await readFile('assets/garden.glb')).toString('base64'),castUrl:'data:model/gltf-binary;base64,'+(await readFile('assets/walking-cast.glb')).toString('base64'),manifest:JSON.parse(await readFile('assets/garden-scene.json','utf8'))};
const inline='<script>window.__GARDEN_PACKED__='+JSON.stringify(packed).replace(/</g,'\\u003c')+';</script><script type="module">'+app+'</script>';
// A function replacement preserves dollar-sign sequences in the bundled code.
await writeFile('standalone.html',html.replace('GARDEN_SCRIPT',()=>inline));
console.log('Built cinematic page and standalone download with embedded Blender assets.');
