# Build log

## 2026-09-15 — separate walking edition and Blender refinement

### Scope

Keep the published 112-second film intact. Build a separate version where Shahaf walks with Neria, holding hands, can look at him, receives affectionate responses when she pauses, and enters the cinematic at the café. Continue improving both the Blender film and the interactive presentation. They currently live separately; sharing a home stays a future hope.

### Implemented

- Added `walk-together/` and `scripts/build_walking.py`. The generated standalone HTML includes the original music.
- Articulated walking figures, shared hand target with two-bone arm solving, step animation, corridor boundaries, keyboard/touch/automatic walking, camera drag, and a close view of him.
- Twelve rotating pause lines, a later gentle invitation to continue, quiet synthesized chimes respecting mute/pause, and short trails of light.
- Five-second café arrival with locked movement, approach to chairs, hand release, seated handoff, and continuation into the existing relationship chapters.
- Retained personalization, offline download, replay, pause, audio, chapter controls during the film, and ending camera movement.
- Added softer character silhouettes, more detailed faces, contact shadows, and matching heads through the seated transition.
- Saved the latest Blender geometry corrections. Added a light-seed opening, 22 drifting petals, 64 grains of gold light, depth-of-field changes, two breathing figures, 12 animated eye components, 117 swaying flowers, 115 drifting fireflies, and 14 floating lanterns.

### Verification actually run

- `python scripts/build_walking.py` and `node --check output/walking-syntax.js` passed after the latest edits.
- Python compile checks passed for the builder, polish, secondary animation, and geometry audit scripts.
- Playwright desktop checks covered forward movement, hand contact, distinct stop responses, sound scheduling and mute, café arrival, and movement locking. No page or WebGL errors were reported.
- Playwright phone checks used actual CDP touch events at 390 × 844: drag movement, release, touch cancellation, look control, modal pause, and café handoff passed. No horizontal document overflow or WebGL errors were reported.
- Further desktop regression checks covered both lateral boundaries, backward boundary, input clearing across pause, camera transition, 112-second ending, ending orbit, and replay reset.
- A downloaded personalized HTML was opened from disk with networking disabled at 375 × 667. Walking, embedded music, the personalized speaker, and reduced-motion particle suppression passed, with no overflow or WebGL errors.
- Native Blender audit after the latest additions: 1,758 objects, 4,717,431 evaluated triangles, 24 path roses, both faces visible in the production view, packed soundtrack, and no invalid drivers at six sampled frames.
- Six Cycles benchmark frames at 1280 × 800 / 48 samples took 6.795, 4.458, 5.490, 5.539, 4.929, and 4.925 seconds. An EEVEE comparison was also rendered; Cycles gave cleaner petal and glass shading.

### Observed problems and corrections

- A wide walking camera orbit put a giant flower between the camera and the couple. Constrained the drag range and changed the look control to a close view from her side of the path.
- Initial character silhouettes narrowed too far at the waist. Added continuous waist geometry and smoother shoulders.
- Phone arrival initially aimed at the unadjusted landscape camera. Matched the portrait distance and field of view before the handoff.
- A touch test initially searched for the hidden keyboard shortcut in the button's accessible name. Corrected the test selector; the control itself was present.
- Blender terrain normals previously faced downward on most faces. Corrected winding; the black ring artifact disappeared.
- A garland reparenting pass read world matrices before dependency-graph evaluation and collapsed blossoms at the origin. Restored explicit anchors and added graph updates before reading transforms.
- Rejected the large distant-ground-plane experiment; its image remains in the render folder.
- The first review-camera batch omitted `import bpy`. Blender's MCP wrapper reported the Python failure inside `structuredContent` while leaving `isError` false. Those incorrectly framed renders are preserved in `renders/failed-review-setup/`; the corrected batch checks the inner status before rendering.

### Open work / next production step

The high-quality Blender scene and the functional browser interaction currently exist separately. Optimize and integrate Blender assets into the browser presentation, then review and refine the complete experience on desktop and phone. A complete rendered movie has not been produced. The new edition has not been committed, pushed, or deployed. The original published HTML is unchanged.

The stock Function validator was run and did not pass. Its diagnostic is in `blender/shahaf-garden/function-gate-diagnostic.txt`. The report includes both the inapplicable Meshy/approved-image requirements and remaining draft-contract fields. This is recorded as incomplete evidence, not a passed gate or a reason to stop authorized local work.

## 2026-09-15 — actual Blender assets in a browser candidate

- Added `garden/`, pinned Three.js 0.186.0 and esbuild 0.28.2, and bundled the renderer locally.
- Added `scripts/export_web.py` under the Blender scene. Export runs against an unsaved background copy and preserves the authoring file. A GLB candidate and instance manifest now exist in `garden/assets/`.
- Added a lower-density botanical sampling option (`detail=0`) to the procedural source. The existing native scene still uses its original sampling levels; the new option is for browser prototypes.
- Exported three flower morph prototypes and 117 instance records rather than duplicating all flower geometry.
- The running browser loaded 973 static meshes and combined them into 48 batches, plus 11 flower batches. A wide frame submitted approximately 1.92 million triangles across all shadow/post-processing passes; this is not yet a passed mobile performance target.
- Confirmed opened petal normals agree with triangle winding for garden, hero, and rose prototypes (zero reversed normals in the sampled complete petal primitives). The first diagnostic assumed every glTF accessor had a buffer view; zero/sparse morph accessors require special handling, so the diagnostic was narrowed to the nonzero petal primitives it was intended to check.
- Rendered shadow-on and shadow-off comparison images after the loading overlay finished fading. Reduced excessive normal bias and increased desktop shadow resolution. Lighting and material work remains in progress.
- The installed Three.js release warned that PCFSoftShadowMap was removed; switched to its supported PCFShadowMap. Added a data-URI favicon to remove a 404 from browser checks.
- Corrected a native rear-ceiling review camera that was inside the service counter. Its black render is retained, and the corrected view has been rendered and inspected.

The `garden/` candidate is currently a static asset/rendering preview. The complete playable prototype remains in `walk-together/`. The next step is restoring cinematic timing and connecting the tested controls to the new Blender asset scene. No new version has been committed or deployed.

## 2026-09-15 — complete Blender-based film and walking modes

### Implemented

- Integrated the 112-second cinematic, all seven chapters, camera motion, music, personalization, replay and ending camera controls into `garden/`.
- Added a mode choice and an ending action for switching between the film and walking experience.
- The walking version begins with the first bloom, then gives control to Shahaf. Neria holds her hand and follows her pace. Stops produce varied affectionate lines, quiet chimes and particles; a longer pause brings “Shall we keep going, my love?”
- Authored a separate walking character scene in Blender, with articulated parts, blinking/smiling faces, standing/seated morphs and a 48-frame pose preview. Its source is `Shahaf_Walking_Characters_v001.blend`.
- Connected those parts to the browser controller. The café arrival locks movement, releases hands, approaches the chairs, sits the characters, slides the chairs toward the table, and continues the film.
- Added a twilight sky, more stars, bloom, selective depth of field, multisampling and responsive end framing. Kept the future-home statement explicitly about someday.
- Added one-file personalized downloads with models, decoder, code and song embedded. The hosted page loads a small shell and streams the song separately.

### Problems found and corrected

- Copied Blender mesh data initially lost object-linked material overrides. Restored the actual material slots before joining parts; retained the failed and corrected portrait renders.
- Thin petals showed unstable self-shadow bands. Baked ambient shading with hemisphere ray tests in Blender and used it for the petals while retaining ground shadows.
- Close-up inspection exposed detached hair waves and a protruding chin shape. Replaced the waves with a connected sculpted scalp and refined the chin volume.
- Shoes could cross a stair boundary between the ankle sample and the toe. Contact now samples the shoe footprint, and an unintended double interpolation during sitting was removed.
- The first standalone package corrupted `$&` sequences in minified JavaScript because a string replacement expanded them. Switched to a function replacement and added exact inline-code comparison to `scripts/verify_garden.py`.
- Windows `.cmd` argument handling split a URL at `&`; the resulting malformed `AT` invocation made no schedule. URL-bearing browser actions now live in script files. A separate inline arrow-function command produced a small redirected log; that log is retained under `output/windows-cmd-quoting-error.log`.
- Landscape speech positioning covered the face. Moved the short-screen dialogue to the side. Portrait framing now keeps the face and both cover characters in view.

### Verification actually run

- A full natural-speed playback reached story time 112 and `finished=true`; audio was still playing and no browser or WebGL errors were recorded. The test elapsed about 115 seconds while other checks also ran.
- Keyboard checks passed for both lateral boundaries, the back boundary, hand contact, varied stop responses, the longer-pause invitation, mute, pause/input clearing, replay reset and paused ending camera movement.
- Stair checks sampled 20 shoe contacts without a sole falling below its supporting surface.
- Real touch events in a 390 × 844 emulated browser passed movement, release, cancellation, look, modal pause, café arrival, ending camera drag and switching back to the film.
- The emulated portrait look view measured 29.2 fps on the test machine; no physical-phone performance claim is made.
- Layouts at 1440 × 900, 390 × 844, 375 × 667 and 844 × 390 had no document overflow, no out-of-bounds ending actions and no browser/WebGL errors. Screenshots were visually inspected.
- The personalized standalone file loaded with networking disabled, played the embedded song, moved the pair, respected reduced motion, preserved `<` and `&` in a name, and made no HTTP requests.
- The artifact verifier passed original-film preservation, exact JavaScript inlining, identical embedded model bytes and identical song bytes.
- Exported geometry was reduced where details occupy only a few screen pixels. The cinematic model bound is 496,586 triangles; additional shadow/post-processing submissions are reported separately.
- Native Blender audit: 1,758 objects, 4,763,079 authoring triangles, packed soundtrack, three clear Boolean aperture rays and both heads visible in the production view.

### Release structure

The original page remains at the existing Pages root. The new cinematic and walking modes share `/garden/`. Generated web artifacts are checked in for static deployment. The original HTML retains SHA-256 `29dbe4d129e29c5f12915aa818cb58cb1666b1fc67e78d81e7834a3d8ab598d0`.

The stock Meshy-oriented room validator remains an inapplicable diagnostic for this zero-credit procedural workflow; it was not marked passed. The applicable checks are recorded in `garden/acceptance.json`.
