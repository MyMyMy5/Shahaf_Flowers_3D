export const END=112,FINALE=100,ORBIT=110;
export const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
export const mix=(a,b,t)=>a+(b-a)*t;
export const smooth=t=>(t=clamp(t),t*t*(3-2*t));
export const between=(t,a,b)=>smooth((t-a)/(b-a));
export const chapters=[
 {at:0,end:11,title:'a little love letter'}, {at:11,end:22,title:'someone likes flowers'},
 {at:22,end:32,title:'a place for us'}, {at:32,end:45,title:'you and me'},
 {at:45,end:69,title:'choosing each other'}, {at:69,end:100,title:'the life we will build'},
 {at:100,end:112,title:'always, my love'}
];
export const captions=[
 [1,5.5,'So… a little reminder.','Of just how much I love you.'],
 [8,13.2,'And I know someone…','…who really likes flowers.'],
 [15.3,20.9,'So I animated a few.','Okay… maybe a whole garden.'],
 [25,30.8,'But why stop at flowers?','When I could imagine us somewhere like this.'],
 [34,39.7,'You, me, and all of this.',"Now that's my kind of evening."],
 [40.8,49,"We’ve had our hard days.","But they haven’t changed how much I love you.",'letter'],
 [50.5,58.5,'I want to love you better.','With more patience. More listening.\nAnd more kindness when we disagree.','letter'],
 [60,68,'You’re so special to me.','Your smile. Your warmth.\nThe little things that make you, you.','letter'],
 [69.5,78.5,'One day, a life like this.','Someday, a place of our own.\nFor now, a stronger us, one day at a time.','letter'],
 [80,89,'Let’s build something strong.','A love we take care of,\nand a future we’re excited to grow into.','letter'],
 [90.5,98.2,'A little better, every day.','You and me, choosing each other.\nThat’s the future I want.','letter']
];
const keys=[
 [0,[-2.6,2.8,13.9],[-2.6,2.42,6.6]], [4,[-2.2,2.95,13.9],[-2.6,2.42,6.6]],
 [10,[.4,3.9,15.0],[-2.6,2.40,6.6]], [15,[6.9,7.3,18.2],[-.7,1.6,1.8]],
 [21,[-6.6,5.9,17.0],[0,1.7,.6]], [27,[-3.4,4.8,12.8],[0,2.7,-1.0]],
 [33,[1.9,4.4,11.8],[0,2.6,-1.0]], [40,[-.3,3.65,9.4],[0,2.55,-.6]],
 [44,[-1.4,4.2,11.4],[0,2.75,-.8]], [51,[5.7,6.5,16.2],[0,3.25,-.8]],
 [60,[2.2,5.1,14.7],[0,2.9,-1.0]], [72,[.8,5.5,15.5],[0,2.9,-1.0]],
 [83,[.2,5.6,16.2],[0,3.0,-.8]], [94,[5.7,6.5,16.2],[0,3.25,-.8]],
 [100,[7.5,6.9,17.3],[-2.8,3.45,-.8]], [115,[7.5,6.9,17.3],[-2.8,3.45,-.8]]
];
function catmull(p0,p1,p2,p3,t){return p1.map((v,i)=>.5*((2*v)+(-p0[i]+p2[i])*t+(2*p0[i]-5*v+4*p2[i]-p3[i])*t*t+(-p0[i]+3*v-3*p2[i]+p3[i])*t*t*t));}
export function cameraAt(t,aspect){
 let j=0;while(j<keys.length-2&&t>keys[j+1][0])j++;
 const a=keys[j],b=keys[j+1],before=keys[Math.max(0,j-1)],after=keys[Math.min(keys.length-1,j+2)],f=clamp((t-a[0])/(b[0]-a[0]));
 let eye=catmull(before[1],a[1],b[1],after[1],f),at=catmull(before[2],a[2],b[2],after[2],f);
 if(aspect<1){const narrow=smooth((1.05-aspect)/.60);at[0]=mix(at[0],0,narrow*between(t,90,100));const factor=mix(1,mix(1.62,1.38,between(t,47,58)),narrow)*mix(.86,1,between(t,11,26));eye=at.map((v,i)=>v+(eye[i]-v)*factor);}
 return [eye,at];
}
