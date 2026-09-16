# Shahaf's garden — Blender authoring scene

`Shahaf_Garden_v001.blend` is the separate Blender version of the love-letter garden. The existing website stays intact.

The scene contains the arched conservatory, table and couple, 24 red path roses, 93 large garden flowers, climbing flowers, butterflies, lanterns, and a heart constellation. Its 112-second camera animation follows the relationship chapters. The soundtrack is packed into the file.

## Authoring

- `scripts/build_scene.py`: procedural source for the scene.
- `scripts/polish_scene.py`: descending seed of light, floating opening petals, gold dust, depth of field, and atmospheric lighting cues.
- `scripts/animate_scene_life.py`: breathing, head motion, blinking, flower sway, firefly drift, and lantern motion.
- `scripts/audit_scene.py`: geometry checks and reproducible engineering/review cameras.
- `scripts/benchmark_render.py`: consecutive Cycles render measurements; does not modify the saved authoring file.
- `scripts/load_helpers.py`: restores MCP helper namespaces after reopening Blender, without rebuilding the scene.
- `scripts/build_walkers.py`: authors articulated walking parts, facial/seated morphs, a native pose preview and the character GLB.
- `scripts/export_web.py`: exports compressed browser assets, reduced detail for tiny props, and baked petal ambient shading.

`Shahaf_Walking_Characters_v001.blend` contains the separate character scene and its 48-frame pose preview.

The scene was built directly by the primary agent using the official Blender MCP connection. All geometry is procedural; no paid generation service or third-party models were used.

## Current evidence

- `geometry-audit.json`: measured topology, opening rays, contact values, animation samples, and camera visibility.
- `lighting-manifest.json`: actual lights and emission materials.
- `secondary-animation.json`: counts of animated details.
- `render-benchmark.json`: six actual frames at 1280 × 800, Cycles/OptiX, 48 samples.
- `renders/production_corrected_v001.png`: corrected Cycles wide view, before the latest small secondary animations.
- `renders/shahaf_garden_release.png`: current Cycles production view with the refined characters and sign.
- `renders/benchmark/`: opening, dinner, and final comparison frames after the first cinematic polish.

Earlier render experiments are retained. In particular, `thumbnail_refined_v001.png` contains a rejected distant-ground experiment, and the earlier opening render contains a terrain-normal defect that has been corrected.

## Browser release

The source scene has 4,763,079 evaluated authoring triangles. Its optimized assets are integrated into `../../garden/`, including the cinematic timing, music, flower morphs, butterflies, lanterns, captions, walking characters and café handoff. The browser renders the film in real time; the editable Blender sources retain their authoring detail.

The stock room-skill validator assumes paid Meshy assets and human image approvals. It is not the release contract for this locally authored, zero-credit scene. Its diagnostic remains recorded. Applicable acceptance checks are documented in `../../garden/acceptance.json`; no Meshy provenance or human approval has been invented.
