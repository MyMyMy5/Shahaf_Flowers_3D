# Walk together

A separate interactive edition of the garden. The original `somewhere-just-us.html` and the published film are preserved.

Open `index.html` directly or visit `http://127.0.0.1:58054/walk-together/` while the local server runs. The generated page includes its code, geometry, and music, so it works offline.

## Experience

- Shahaf leads the pair along the stone path. Neria matches her pace and holds her hand.
- Use WASD or arrow keys, the phone joystick, or the **Walk with me** button.
- **Look at him** / **E** moves into her viewpoint. Select it again to return to the path.
- Drag the garden for a small camera adjustment.
- After a new pause, Neria turns toward her and a new affectionate line appears. Quiet chimes and particles accompany it when sound and motion are enabled.
- On arrival, movement ends, they approach their chairs, and the film continues through the relationship chapters and lantern ending.
- Pause, mute, personalize, offline download, ending camera movement, and replay are retained.

## Source and build

`src/walk.js`, `src/walk.css`, and `src/controls.html` contain the interactive additions. Run:

```powershell
python scripts/build_walking.py
node --check output/walking-syntax.js
```

The build script reads the original film and creates this edition using checked integration points. It never writes the original film. Edit the source files and rebuild; avoid editing the generated HTML.

## Current scope

This is the preserved interaction prototype in the original custom WebGL renderer. The completed Blender-based cinematic and walking experience is in `../garden/`; use that version for the current presentation. This prototype remains useful as a small standalone reference for the original movement implementation.

Browser checks and screenshots are in the ignored `output/playwright/` folder. A test-only state hook is available with `?test=1`; normal URLs do not expose it.
