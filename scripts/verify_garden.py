"""Verify the generated deliverables, including the offline packaging regression."""
from pathlib import Path
import base64
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
garden=ROOT/'garden'
original=(ROOT/'somewhere-just-us.html').read_bytes()
assert hashlib.sha256(original).hexdigest()=='29dbe4d129e29c5f12915aa818cb58cb1666b1fc67e78d81e7834a3d8ab598d0','Original film changed from the published baseline'
online=(garden/'index.html').read_text(encoding='utf-8')
standalone=(garden/'standalone.html').read_text(encoding='utf-8')
assert len(online)<40000 and 'src="../assets/song.mp3"' in online,'Online shell/music path regression'
assert 'GARDEN_SCRIPT' not in standalone,'Inline code was corrupted by a replacement marker'
module_start=standalone.index('<script type="module">')+len('<script type="module">')
module_end=standalone.index('</script>',module_start)
expected=re.sub(r'</script',r'<\\/script',(garden/'app.js').read_text(encoding='utf-8'),flags=re.I)
assert standalone[module_start:module_end]==expected,'Bundled JavaScript changed during inlining'
packed_start=standalone.index('window.__GARDEN_PACKED__=')+len('window.__GARDEN_PACKED__=')
packed_end=standalone.index(';</script>',packed_start)
packed=json.loads(standalone[packed_start:packed_end])
for key,name in [('url','garden.glb'),('castUrl','walking-cast.glb')]:
    assert base64.b64decode(packed[key].split(',',1)[1])==(garden/'assets'/name).read_bytes(),f'Embedded {name} differs'
music=base64.b64decode(re.search(r'<audio id="music" src="data:audio/mpeg;base64,([^"]+)',standalone)[1])
assert music==(ROOT/'assets/song.mp3').read_bytes(),'Embedded soundtrack differs'
assert len(packed['manifest']['flowers'])==117
report={'originalFilmUnchanged':True,'originalSha256':hashlib.sha256(original).hexdigest(),'inlineJavaScriptUnchanged':True,'embeddedModelsMatch':True,'embeddedMusicMatches':True,'onlineBytes':(garden/'index.html').stat().st_size,'standaloneBytes':(garden/'standalone.html').stat().st_size,'flowers':117}
(ROOT/'output'/'garden-artifact-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
