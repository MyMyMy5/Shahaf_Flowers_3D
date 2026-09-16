# Shahaf_Flowers_3D

A personal, animated love letter for Shahaf: blooming flowers, a candlelit table for two, and a soundtrack.

## Choose an experience

- [Blender garden — the film](https://mymymy5.github.io/Shahaf_Flowers_3D/garden/)
- [Blender garden — walk together](https://mymymy5.github.io/Shahaf_Flowers_3D/garden/?mode=walk)
- [The original film](https://mymymy5.github.io/Shahaf_Flowers_3D/)

The new garden uses models authored in Blender. It offers the cinematic love letter and a walking version: Shahaf leads the pair along the path while they hold hands, can look at Neria, and receives affectionate responses when she pauses. At the café, the characters sit down and the film continues.

On a computer, use WASD or the arrow keys to walk and **E** to look at him. On a phone, use the thumb control and **Look at him** button. **Walk with me** also follows the path automatically. The ending lets you replay or switch experiences.

The pencil menu personalizes the names and final message. **Save her website** downloads one HTML file containing both modes, the models, and the music; it works offline.

The original `somewhere-just-us.html` remains unchanged.

The seven-chapter film runs for 1 minute 52 seconds. Its later chapters focus on caring for the relationship and looking forward to a future together.

## Open the experience

Open `somewhere-just-us.html` in a modern browser, then select **Open when you're ready**. No installation or build step is needed.

The page includes the animation and music, so the HTML file also works offline and can be shared on its own.

## GitHub Pages

The [live website](https://mymymy5.github.io/Shahaf_Flowers_3D/) is published automatically when changes are pushed to `main`.

The Pages workflow keeps the original film at the main URL and publishes the new experience under `/garden/`. You can also run **Deploy to GitHub Pages** manually from the repository's Actions tab.

## Controls

- Use the sound button to turn the music on or off.
- Pause and resume with the playback button.
- Jump between scenes using the chapter controls along the bottom.
- At the ending, move the mouse left or right, or drag horizontally on a phone, to look around the scene.
- Use the pencil button to personalize the names and final message, then select **Save her website** to download a personalized copy with the music included.
- Select **One more time** at the end to replay the experience.

## Files

- `somewhere-just-us.html` — the complete standalone experience.
- `assets/song.mp3` — the soundtrack, also embedded in the HTML for offline sharing.
- `.github/workflows/deploy-pages.yml` — automatic GitHub Pages deployment.
- `garden/` — the Blender-based browser experience, source, bundled page and offline download.
- `blender/shahaf-garden/` — editable Blender scenes, procedural source, export tools and review evidence.
- `walk-together/` — the preserved interaction prototype in the original renderer.
- `BUILD_LOG.md` — implementation history, observed problems and corrections.

See [garden/README.md](garden/README.md) for build instructions and browser checks.

The animation uses WebGL and JavaScript. Enable hardware acceleration in your browser if the garden cannot load.
