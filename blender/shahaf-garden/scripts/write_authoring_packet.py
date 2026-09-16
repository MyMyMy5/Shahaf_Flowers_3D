"""Record real procedural provenance and incomplete runtime gates honestly."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'geometry-audit.json').read_text())


def write(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


write('room-brief.json',{
 'schema':'game-room.room-brief.v1','roomId':'shahaf-garden','family':'custom',
 'purpose':'A hopeful love-letter garden and candlelit table for Neria and Shahaf. Sharing a home is a future hope.',
 'runtimeSurface':'Separate cinematic and interactive browser editions; current Blender file is the authoring scene.',
 'boundsMeters':[30,30,16],
 'hero':{'id':'table_and_couple','role':'emotional focus','reservedBoundsMeters':[3.7,2.4,2.2]},
 'symmetry':{'mode':'bilateral','order':2,'appliesTo':['conservatory facade','table seating','rose rows'],'exceptions':['curved approach','natural planting','camera compositions']},
 'circulation':{'description':'Open canopy arrival from the curved stone walkway, followed by access to either chair. Walking prototype follows the path and releases controls at the terrace.','minimumClearanceMeters':1.5},
 'productionCamera':{'viewport':[1600,1000],'location':audit['production_camera']['location'],'target':[-2.8,.8,3.45],'verticalFovDegrees':42},
 'performanceBudget':{'maxSceneTriangles':500000,'maxVLowBytes':20000000,'maxHighTextureBytes':24000000,'status':'future browser targets; current authoring triangles exceed target'},
 'creditBudget':{'maximumCredits':0,'approvalRequired':False},
 'environment':{'type':'procedural','identity':'blue hour garden','source':'scripts/build_scene.py and scripts/polish_scene.py','assignmentKey':'SF3D_Midnight_world'},
 'artifacts':{'floorPlan':'renders/review_current_floor_plan.png','reflectedCeilingPlan':'renders/review_current_reflected_ceiling.png','planMetadata':'plan-metadata.json','wallElevations':['renders/review_current_facade_elevation.png'],'visualTarget':'renders/production_corrected_v001.png','openingContactSheet':''}
})
write('props.json',{
 'schema':'game-room.prop-manifest.v1','roomId':'shahaf-garden',
 'generation':{'provider':'local-procedural','apiModel':None,'pricingSource':None,'pricingVerifiedAt':None,'creditsPerTexturedTask':0,'hardCreditCeiling':0,'maxChargedAttemptsPerAsset':0},
 'assets':[{'id':id,'provenance':'Procedurally authored by primary agent in Blender','source':'scripts/build_scene.py','status':'authoring','externalModel':False} for id in ['arched_conservatory','stone_terrace','table_and_chairs','neria','shahaf','garden_blossoms','path_roses','climbing_flowers','butterflies','paper_lanterns']],
 'notes':'No Meshy service, generated reference image, purchased mesh, or external HDRI was used.'
})
write('openings.json',{
 'schema':'game-room.opening-schedule.v1','roomId':'shahaf-garden',
 'primaryArrival':{'openingId':'open_canopy_front','exception':'The broad, open front canopy is the arrival; the rear service door is not the walking entrance.'},
 'openings':[{'id':'open_canopy_front','type':'open-front','width':6.7,'clear':True}]+[{'id':o['id'],'type':'exact-boolean','width':o['width'],'height':o['height'],'centerRayClear':o['center_ray_clear'],'sourceObject':'SF3D_Facade_structure'} for o in audit['opening_checks']]
})
write('room-layout.json',{
 'schema':'game-room.layout.v1','roomId':'shahaf-garden','units':'meters',
 'surfaces':[{'id':'garden','shape':'circular terrain','radius':15},{'id':'terrace','shape':'round platform','center':[0,1.2,0.2],'radius':4.1},{'id':'canopy','bounds':[6.8,4.1,5.32]}],
 'instances':[{'id':'table_and_couple','center':[0,-.65,.245]},{'id':'path_roses','count':24,'arrangement':'both sides of the curved walkway'},{'id':'garden_flowers','count':93}],
 'productionCamera':{'location':audit['production_camera']['location'],'target':[-2.8,.8,3.45],'verticalFovDegrees':42}
})
reviews={}
for gate in ('function','form','runtime'):
 reviews[gate]={'status':'pending','approvedBy':'','approvedAt':'','evidence':['geometry-audit.json','lighting-manifest.json','README.md'],'strangestElement':'Oversized fantasy flowers surrounding a miniature conservatory.','notes':'User authorized autonomous local construction. No human milestone approval is being fabricated. Runtime integration remains incomplete.'}
write('milestone-reviews.json',{'schema':'game-room.milestone-reviews.v1','roomId':'shahaf-garden',**reviews})
write('plan-metadata.json',{
 'schema':'game-room.plan-metadata.v1','roomId':'shahaf-garden','style':'monochrome-engineering','projectionSource':'actual-meshes',
 'layers':['lower-room','reflected-ceiling'],'semanticLabelsOutsideImage':True,'aiInspirationIncluded':False,
 'aiInspirationReason':'The existing user-approved WebGL garden provided the visual direction; all Blender geometry is procedural.',
 'coverage':['floor_plan','reflected_ceiling','facade_elevation']
})
old=json.loads((ROOT/'legacy-meshy-report.json').read_text())
old['status']='authoring review; goal and runtime integration incomplete'
old['formChecks'].update({'primaryArrival':True,'manifold':True,'booleans':True,'camera':True,'provenance':True})
old['reviewRenders']={'corners':['renders/review_current_corner_'+s+'.png' for s in ('front_left','front_right','rear_left','rear_right')],'ceiling':['renders/review_current_ceiling_'+s+'.png' for s in ('center_up','oblique_front','oblique_rear')],'environment':{'cycles':'renders/production_corrected_v001.png','eevee_comparison':'renders/eevee_comparison_v001.png'}}
old['runtimeChecks'].update({'lightingManifest':True,'browserCapture':'../../output/playwright/walk-his-face-phone.png','errors':['Blender assets have not yet been optimized or integrated into the browser prototype.']})
old['postmortem']={
 'observations':['The Blender scene has 4,717,431 evaluated triangles.','The original published film remains intact.','Walking mechanics work in a separate custom-WebGL edition.'],
 'corrections':['Terrain face winding corrected.','Garland world transforms restored after dependency graph evaluation.','Physical contacts and hanging fixtures adjusted.','Close walking camera replaced a view obstructed by a large flower.','Portrait café handoff now matches camera distance and field of view.'],
 'remainingRisks':['No complete rendered movie yet.','Authoring geometry exceeds the intended browser budget.','A full-scene collision audit has not been performed.','Human milestone approvals are not recorded; the stock Meshy validator does not match the local procedural workflow.']}
write('legacy-meshy-report.json',old)
print('Wrote authoring packet with runtime gates pending.')
