# Browser checks

Run from the repository root with the local HTTP server available. These are Playwright CLI scripts, using real keyboard, pointer, touch, media and DOM behavior.

```powershell
New-Item -ItemType Directory -Force output/playwright | Out-Null
npx.cmd --yes --package @playwright/cli playwright-cli -s=garden open http://127.0.0.1:58054/garden/?test=1 --browser chrome
npx.cmd --yes --package @playwright/cli playwright-cli -s=garden run-code --filename garden/qa/interactions.cjs
npx.cmd --yes --package @playwright/cli playwright-cli -s=garden run-code --filename garden/qa/touch.cjs
npx.cmd --yes --package @playwright/cli playwright-cli -s=garden run-code --filename garden/qa/layouts.cjs
npx.cmd --yes --package @playwright/cli playwright-cli -s=garden run-code --filename garden/qa/playthrough.cjs
```

Open the deployed garden instead to run the same checks against GitHub Pages. The scripts derive their base URL from the current garden page. The playthrough check runs the full film at normal speed.

Artifact checks:

```powershell
python scripts/verify_garden.py
```

The artifact check verifies that the original film is untouched, inlined JavaScript remains byte-for-byte correct after script escaping, and both models and the song are embedded correctly in the standalone download.

Offline behavior was also checked by downloading a personalized file, opening it from disk in a browser context with networking disabled, and verifying movement, names containing `<` and `&`, music playback, reduced motion and zero HTTP requests. Repeat this from the pencil menu after changing the download flow.

Phone-size tests emulate layout and touch input on the test machine. Their frame rates do not establish performance on physical phones.
