# Our little garden

A Blender-authored flower garden with two ways to experience the love letter:

- **Watch our little film:** a seven-chapter, 112-second cinematic.
- **Walk together:** watch the first flower bloom, then lead the couple toward their table while holding hands. Pauses bring a new affectionate line, a quiet chime and a small burst of light. At the café, movement locks, the chairs slide out, the couple sits, and the cinematic continues.

The original film and the earlier walking prototype remain available in their own files.

## Open and use

Use the [film](https://mymymy5.github.io/Shahaf_Flowers_3D/garden/) or [walking link](https://mymymy5.github.io/Shahaf_Flowers_3D/garden/?mode=walk). For local development, serve the repository with `python -m http.server 58054 --bind 127.0.0.1`, then open `/garden/` on that server.

Keyboard: WASD / arrows to walk, **E** to look at him, and Space to pause. Touch controls include a thumb pad, a look button, and an automatic walking button. At the ending, move the mouse horizontally or drag on a phone to look around.

The pencil menu changes the names and last line. Its download embeds the complete code, compressed models and soundtrack in one HTML file. No server or network is needed to open that downloaded file.

## Build

```powershell
cd garden
npm ci
npm run build
cd ..
python scripts/verify_garden.py
```

Three.js 0.186.0 and esbuild 0.28.2 are pinned. The browser bundle includes its model decoder and uses no CDN. The online shell streams the existing song from `../assets/song.mp3`; the standalone download embeds it.

## Source

- `src/main.js`: scene loading, lighting, batching, flower growth, particles, sky and cinematic rendering.
- `src/story.js`: camera path, chapters and relationship captions.
- `src/presentation.js`: playback, sound, personalization, keyboard navigation and downloads.
- `src/walking.js`: articulated character posing, movement, hand contact, stop responses and café arrival.
- `build.mjs`: creates `app.js`, `index.html` and `standalone.html`.
- `qa/`: browser checks using Playwright CLI.

The garden and characters are exported from the separate Blender sources with `blender/shahaf-garden/scripts/export_web.py` and `build_walkers.py`. Export runs in a background copy and does not overwrite the garden authoring file.

## Rendering choices

The browser uses 117 flower instances, including 24 red path roses. Three morph-capable flower prototypes share geometry. Small props receive appropriate geometry reduction, while the first bloom and the walking faces retain more detail. Compressed model buffers, batched static meshes, multisampling, dynamic shadows, bloom and selective depth of field keep the scene detailed and responsive.

Thin petals use ambient shading baked from their opened Blender geometry. This avoids unstable self-shadow bands while retaining shadows on the ground. The sky and air are procedural browser effects; they do not require a downloaded environment image.

The release model assets total approximately 4.9 MB. The standalone HTML is approximately 11.3 MB, including the music. The fully grown cinematic scene has a computed maximum of 496,586 model triangles; shadow and post-processing passes submit additional triangles.

## Verification

The full film was played through at normal speed and reached its ending with audio and no browser/WebGL errors. Checks covered desktop, portrait, small-phone and landscape layouts; keyboard and real touch events; hand contact; dialogue variation; audio mute; pause; touch cancellation; café arrival; replay; ending camera movement; and switching experiences.

A personalized download was opened with networking disabled. Embedded music, models, movement, reduced motion and names containing `<` and `&` worked without HTTP requests. The artifact verifier checks model/music bytes and exact JavaScript preservation during HTML packaging.

Phone-size frame-rate measurements use an emulated viewport on the test machine, not a physical phone. See `qa/README.md`, `acceptance.json` and the root `BUILD_LOG.md` for the scope of the evidence.

Primary implementation references: [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), [InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html), [WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html), and the installed Blender/Three.js source and APIs.
