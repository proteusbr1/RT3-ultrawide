'use strict';
// RT3 Steam executable C6E178BF...; addresses verified against unpacked live image.
const base = Process.getModuleByName('RT3.exe').base;
const at = va => base.add(va - 0x400000);
const signatures = [
  [0x538b60, '51568bf18a86680c'],
  [0x51f460, '568bf18b4e5881f9'],
  [0x51f370, '568bf18b4e5881f9'],
  [0x51f2b0, '8b515881fae02e00'],
  [0x53fe90, '83ec40538b5c2448'],
  [0x5581e0, '8b4133a8027408b8'],
  [0x5582f0, '56578b7c241485ff'],
  [0x4de140, '8b5424048b0281ec'],
  [0x538f10, '81ecd00000005355'],
  [0x477c10, '8b413383ec10a900'],
  [0x53fda0, '578bf98b475c85c0'],
  [0x548180, '83ec18538bd98b83'],
  [0x552560, '83ec188b44241c56'],
  [0x45f420, '81ec180200005657'],
  [0x439e40, '83ec345355568bf1'],
  [0x52d140, '8b4424048b542408']
];
for (const [va, expected] of signatures) {
  const actual = Array.from(new Uint8Array(at(va).readByteArray(expected.length / 2)), b => b.toString(16).padStart(2, '0')).join('');
  if (actual !== expected) throw Error('Unsupported code or another hook at ' + va.toString(16) + ': ' + actual);
}

const state = Memory.alloc(128);
state.writeByteArray(new Uint8Array(128));
state.writeU32(Math.round(SCALE_X * 1048576));
state.add(24).writeU32((1048576-state.readU32())*8);
state.add(28).writeU32((1048576-state.readU32())*8);
// Split the original left skin at the wood/green transition. Keep texture UVs,
// and draw the green tail at the right anchor before information controls.
const HUD_SPLIT=0.4;
const HUD_BOTTOM=0.954;
const HUD_Y=1-HUD_BOTTOM;
state.add(64).writeS32(Math.round(HUD_Y*16777216));
const menuArt = typeof MENU_ART === 'undefined' ? null : MENU_ART;
if (menuArt) {
  const aspect = (4 / 3) / SCALE_X, artAspect = menuArt.image_width / menuArt.image_height;
  // Uniform cover: narrower screens crop the sides; wider screens crop below.
  const visibleWidth = Math.min(menuArt.image_width, menuArt.image_height * aspect);
  const visibleHeight = Math.min(menuArt.image_height, menuArt.image_width / aspect);
  const left = (menuArt.image_width - visibleWidth) / 2;
  [left / menuArt.texture_width, 0,
   (left + visibleWidth) / menuArt.texture_width, visibleHeight / menuArt.texture_height]
    .forEach((v, i) => state.add((21 + i) * 4).writeFloat(v));
  state.add(104).writeU32(1);
}
const splitSkin=new NativeCallback((renderer,a)=>{
  const x1=a.readFloat(),y1=a.add(4).readFloat(),x2=a.add(8).readFloat(),y2=a.add(12).readFloat();
  if(x2<=x1 || y2<=y1)return;
  const u1=a.add(28).readFloat(),u2=a.add(36).readFloat(),v1=a.add(32).readFloat(),v2=a.add(40).readFloat();
  const depth=state.add(16).readS32(),skin=state.add(48).readU32();
  const emit=(left,top,right,bottom,anchor)=>{
    left=Math.max(x1,left);right=Math.min(x2,right);top=Math.max(y1,top);bottom=Math.min(y2,bottom);
    if(right<=left || bottom<=top)return;
    const u=x=>u1+(u2-u1)*(x-x1)/(x2-x1),v=y=>v1+(v2-v1)*(y-y1)/(y2-y1);
    quad(renderer,left*SCALE_X+anchor,top+HUD_Y,right*SCALE_X+anchor,bottom+HUD_Y,
      a.add(16).readFloat(),a.add(20).readU32(),a.add(24).readPointer(),u(left),v(top),u(right),v(bottom),a.add(44).readU32());
  };
  state.add(16).writeS32(0);
  try{
    if(skin===1){
      if(state.add(60).readU32())emit(HUD_SPLIT,Math.max(y1,0.6975),x2,HUD_BOTTOM,1-SCALE_X);
      // Follow the outer edge of the nine buttons and the wider lower buttons.
      emit(x1,y1,0.388,0.89,0);
      emit(x1,0.89,0.394,HUD_BOTTOM,0);
    }else if(state.add(60).readU32())emit(x1,y1,x2,HUD_BOTTOM,1-SCALE_X);
  }finally{state.add(16).writeS32(depth);}
  // All visible fragments were emitted above. Suppress the original full quad.
  a.add(8).writeFloat(x1);
},'void',['pointer','pointer']);
const native = new CModule(`
#include <gum/guminterceptor.h>
extern unsigned int state[];
extern void split_skin(void *renderer,unsigned int *args);
#define draw_depth (*(int *)(state + 4))
#define input_depth (*(int *)(state + 5))
#define draw_offset state[6]
#define input_offset state[7]
#define draw_y (*(int *)(state+13))
#define input_y (*(int *)(state+14))
typedef struct { unsigned int *p; unsigned int saved; int changed; int depth; unsigned int offset; unsigned int skin; int y; unsigned int saved_y; } Saved;
/* Integer-only IEEE754 conversion avoids the target's x87 stack and flags. */
static int fixed(unsigned int bits) {
  int e=(int)((bits>>23)&255)-126;
  unsigned int m=(bits&0x7fffff)|0x800000;
  unsigned int v;
  if (((bits>>23)&255)==0) return 0;
  if (e>5 || e < -30) return 0;
  v=e>=0 ? m<<e : m>>(-e);
  return bits>>31 ? -(int)v : (int)v;
}
static unsigned int ieee(int value) {
  unsigned int sign=value<0?0x80000000:0;
  unsigned int m=value<0?-value:value;
  int e=126;
  if (!m) return 0;
  while(m>=0x1000000){m>>=1;e++;}
  while(m<0x800000){m<<=1;e--;}
  return sign|((unsigned int)e<<23)|(m&0x7fffff);
}
unsigned int translate_y(unsigned int value,int delta){return ieee(fixed(value)+delta);}
static unsigned int forward_at(unsigned int value, unsigned int offset) {
  long long v=fixed(value);
  return ieee((int)((v*state[0])/1048576)+(int)offset);
}
static unsigned int inverse_at(unsigned int value, unsigned int offset) {
  long long v=(long long)fixed(value)-(int)offset;
  return ieee((int)(v*1048576/state[0]));
}
static unsigned int forward(unsigned int value) { return forward_at(value,draw_offset); }
static unsigned int inverse(unsigned int value) { return inverse_at(value,input_offset); }
static unsigned int window_offset(unsigned char *w) {
  unsigned int vt, firstx, firsty, n, right=0, other=0;
  unsigned char *c;
  if(!w) return (1048576-state[0])*8;
  vt=*(unsigned int *)w;
  if(vt==0x5d0eb8 || vt==0x5d0ed0 || vt==0x5d0f3c) return 0;
  /* TrainDetail and WorldOverview use non-fullscreen HUD window bounds. */
  if(vt==0x5d1990 || vt==0x5d13b4) return (1048576-state[0])*16;
  /* Only full-screen HUD windows with their first control in the lower right. */
  if(*(unsigned int *)(w+5)==0 && *(unsigned int *)(w+9)==0 && *(unsigned int *)(w+13)==0x3f800000 && *(unsigned int *)(w+17)==0x3f800000){
    c=*(unsigned char **)(w+0x70);
    if(c){firstx=*(unsigned int *)(c+11);firsty=*(unsigned int *)(c+15);
      if(firstx>=0x3ec28f5c && firstx<=0x3f800000 && firsty>=0x3f147ae1 && firsty<=0x3f800000) return (1048576-state[0])*16;
    }
    for(n=0;c && n<256;n++,c=*(unsigned char **)(c+0x8e)){
      if(*(unsigned short *)(c+6)!=1)continue;
      firstx=*(unsigned int *)(c+11);firsty=*(unsigned int *)(c+15);
      if(firstx>=0x3ec28f5c && firstx<=0x3f800000 && firsty>=0x3f147ae1 && firsty<=0x3f800000)right++;else other++;
    }
    if(right && !other)return (1048576-state[0])*16;
  }
  return (1048576-state[0])*8;
}
static int right_hud(unsigned char *w){
  unsigned int vt=w?*(unsigned int *)w:0;
  return w && vt!=0x5d0eb8 && vt!=0x5d0ed0 && vt!=0x5d0f3c && state[0]!=1048576 && window_offset(w)==(1048576-state[0])*16;
}
static int window_y(unsigned char *w){return w && (*(unsigned int *)w==0x5d0eb8 || right_hud(w))?(int)state[16]:0;}
static int control_y(unsigned char *c){
  unsigned char *w=*(unsigned char **)(c+0x86);
  if(w && *(unsigned int *)w==0x5d0eb8 && *(unsigned short *)(c+4)==2007)return 0;
  return window_y(w);
}
void update_hud(void){
  unsigned char *manager=*(unsigned char **)0x6d401c,*w=manager?*(unsigned char **)manager:0;
  unsigned int n;state[15]=0;
  for(n=0;w && n<50;n++,w=*(unsigned char **)(w+0x58)){
    if(*(unsigned int *)(w+0x5c) && right_hud(w)){state[15]=1;break;}
  }
}
/* Keep the logical camera rectangle consistent with the expanded device viewport.
 * Labels, projection, culling and world picking also consume this rectangle. */
void update_camera(void){
  unsigned char *camera=*(unsigned char **)0x62be68;
  unsigned int bottom;
  if(state[20] || !camera || *(unsigned int *)camera!=0x5ca078) return;
  bottom=*(unsigned int *)(camera+0x5c);
  if(*(unsigned int *)(camera+0x50)==0 && *(unsigned int *)(camera+0x54)==0 &&
     *(unsigned int *)(camera+0x58)==0x3f800000 && bottom>=0x3f266666 && bottom<=0x3f4ccccd){
    state[17]=(unsigned int)camera;state[18]=bottom;state[19]++;
    *(unsigned int *)(camera+0x5c)=0x3f800000;
    camera[0x64]=1;camera[0x65]=1;
  }
}
void camera_rect(GumInvocationContext *ic){
  unsigned char *camera=(unsigned char *)ic->cpu_context->ecx;
  unsigned int *a=(unsigned int *)(ic->cpu_context->esp+4);
  if(!state[20] && camera==*(unsigned char **)0x62be68 && *(unsigned int *)camera==0x5ca078 &&
     a[0]==0 && a[1]==0 && a[2]==0x3f800000 && a[3]>=0x3f266666 && a[3]<=0x3f800000){
    state[17]=(unsigned int)camera;state[18]=a[3];state[19]++;
    a[3]=0x3f800000;camera[0x64]=1;camera[0x65]=1;
  }
}
static unsigned int control_offset(unsigned char *c) {
  unsigned char *w=*(unsigned char **)(c+0x86);
  unsigned int vt=w?*(unsigned int *)w:0;
  unsigned int id=*(unsigned short *)(c+4);
  if(vt==0x5d0eb8 && id==2058) return (1048576-state[0])*16;
  if(vt==0x5d0eb8 && (id==2005 || id==2007)) return (1048576-state[0])*8;
  if(vt==0x5d0f3c && *(unsigned int *)(c+11)>0x3f000000) return (1048576-state[0])*16;
  return window_offset(w);
}
void window_draw_enter(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  s->offset=draw_offset;draw_offset=window_offset((unsigned char *)ic->cpu_context->ecx);
  s->skin=state[12];state[12]=0;s->changed=0;
  s->y=draw_y;draw_y=window_y((unsigned char *)ic->cpu_context->ecx);
}
void control_draw_enter(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  s->offset=draw_offset;draw_offset=control_offset((unsigned char *)ic->cpu_context->ecx);
  s->y=draw_y;draw_y=control_y((unsigned char *)ic->cpu_context->ecx);
  {unsigned char *c=(unsigned char *)ic->cpu_context->ecx,*w=*(unsigned char **)(c+0x86);
   unsigned int id=*(unsigned short *)(c+4),vt=w?*(unsigned int *)w:0;
   s->skin=state[12];state[12]=vt==0x5d0eb8?(id==2057?1:(id==2058?2:0)):0;
   if(state[26] && vt==0x5d1664 && id==3022)state[12]=3;
   s->changed=(vt==0x5d0eb8 && id==2005) || (vt==0x5d0f3c && (id==31011 || id==31012 || id==31013));
   if(state[26] && vt==0x5d1664 && (id==3023 || id==3024 || id==3422))s->changed=1;
   if(s->changed){s->p=(unsigned int *)(c+0x68);s->saved=*s->p;*s->p &= ~1u;}}
}
void scope_draw_leave(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));draw_offset=s->offset;draw_y=s->y;state[12]=s->skin;if(s->changed)*s->p=s->saved;
}
void selftest(void) { state[8]=forward(0); state[9]=forward(0x3f800000); state[10]=inverse(state[8]); }
unsigned int test_forward(unsigned int x){return forward(x);}
unsigned int test_inverse(unsigned int x){return inverse(x);}
void draw_enter(GumInvocationContext *ic) { draw_depth++; }
void draw_leave(GumInvocationContext *ic) { draw_depth--; }
void primitive(GumInvocationContext *ic) {
  unsigned int *a;
  if (!draw_depth) return;
  a=(unsigned int *)(ic->cpu_context->esp+4);
  a[0]=forward(a[0]);a[2]=forward(a[2]);
  a[1]=translate_y(a[1],draw_y);a[3]=translate_y(a[3],draw_y);state[2]++;
}
void quad_primitive(GumInvocationContext *ic){
  if(draw_depth && state[12]==3){
    unsigned int *a=(unsigned int *)(ic->cpu_context->esp+4);
    a[0]=0;a[1]=0;a[2]=0x3f800000;a[3]=0x3f800000;
    a[7]=state[21];a[8]=state[22];a[9]=state[23];a[10]=state[24];
    state[25]++;return;
  }
  if(draw_depth && state[12])split_skin((void *)ic->cpu_context->ecx,(unsigned int *)(ic->cpu_context->esp+4));
  primitive(ic);
}
void triangle(GumInvocationContext *ic) {
  unsigned int *a;
  if (!draw_depth) return;
  a=(unsigned int *)(ic->cpu_context->esp+4);
  a[0]=forward(a[0]);a[2]=forward(a[2]);a[4]=forward(a[4]);
  a[1]=translate_y(a[1],draw_y);a[3]=translate_y(a[3],draw_y);a[5]=translate_y(a[5],draw_y);
}
void event_enter(GumInvocationContext *ic) {
  unsigned char *event=gum_invocation_context_get_nth_argument(ic,0);
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  s->changed=0;
  s->offset=input_offset;s->y=input_y;
  if(!input_depth){input_offset=window_offset((unsigned char *)ic->cpu_context->ecx);input_y=window_y((unsigned char *)ic->cpu_context->ecx);}
  if(!input_depth && event){s->p=(unsigned int *)(event+36);s->saved=*s->p;*s->p=inverse(s->saved);s->saved_y=s->p[1];s->p[1]=translate_y(s->saved_y,-input_y);s->changed=1;}
  input_depth++;
}
void event_leave(GumInvocationContext *ic) {
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  input_depth--;if(s->changed){*s->p=s->saved;s->p[1]=s->saved_y;}input_offset=s->offset;input_y=s->y;
}
void hit(GumInvocationContext *ic) {
  unsigned int *a=(unsigned int *)(ic->cpu_context->esp+4);
  unsigned char *c=(unsigned char *)ic->cpu_context->ecx,*w=*(unsigned char **)(c+0x86);
  unsigned int id=*(unsigned short *)(c+4);
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  /* The original transparent right-HUD blocker must not cover the free map. */
  s->changed=w && *(unsigned int *)w==0x5d0eb8 && (id==2075 || (id==2058 && !state[15]));
  if(!input_depth){a[0]=inverse_at(a[0],control_offset((unsigned char *)ic->cpu_context->ecx));a[1]=translate_y(a[1],-control_y((unsigned char *)ic->cpu_context->ecx));}
}
void hit_leave(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  if(s->changed)gum_invocation_context_replace_return_value(ic,(void *)0);
}
void hit_outer_enter(GumInvocationContext *ic){hit(ic);input_depth++;}
void hit_outer_leave(GumInvocationContext *ic){input_depth--;hit_leave(ic);}
void world_enter(GumInvocationContext *ic){
  unsigned char *event=gum_invocation_context_get_nth_argument(ic,0);
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  s->depth=input_depth;
  s->changed=input_depth && event;
  if(s->changed){s->p=(unsigned int *)(event+36);s->saved=*s->p;*s->p=forward_at(s->saved,input_offset);s->saved_y=s->p[1];s->p[1]=translate_y(s->saved_y,input_y);}
  input_depth=0;
}
void world_leave(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  if(s->changed){*s->p=s->saved;s->p[1]=s->saved_y;}
  input_depth=s->depth;
}
void modal_enter(GumInvocationContext *ic){Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));s->depth=input_depth;input_depth=0;}
void modal_leave(GumInvocationContext *ic){Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));input_depth=s->depth;}
void minimap_point(GumInvocationContext *ic){
  /* This loop obtains physical coordinates from InputManager, not the UI event. */
  if((unsigned int)gum_invocation_context_get_return_address(ic)==0x478d12){
    unsigned int *a=(unsigned int *)(ic->cpu_context->esp+4);
    a[0]=inverse_at(a[0],control_offset((unsigned char *)ic->cpu_context->ecx));a[1]=translate_y(a[1],-control_y((unsigned char *)ic->cpu_context->ecx));state[11]++;
  }
}
void cursor_enter(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  s->changed=(unsigned int)gum_invocation_context_get_return_address(ic)==0x53f633;
  if(s->changed){
    unsigned int *a=(unsigned int *)(ic->cpu_context->esp+4);
    s->offset=draw_offset;s->depth=draw_depth;s->y=draw_y;draw_y=0;
    draw_offset=(unsigned int)((long long)fixed(a[0])*(1048576-state[0])/1048576);
    draw_depth++;
  }
}
void cursor_leave(GumInvocationContext *ic){
  Saved *s=gum_invocation_context_get_listener_invocation_data(ic,sizeof(Saved));
  if(s->changed){draw_offset=s->offset;draw_depth=s->depth;draw_y=s->y;}
}
`, {state,split_skin:splitSkin});
new NativeFunction(native.selftest,'void',[])();
const test=[32,36,40].map(o=>state.add(o).readFloat());
if(Math.abs(test[0]-(1-SCALE_X)/2)>0.00001 || Math.abs(test[1]-(1+SCALE_X)/2)>0.00001 || Math.abs(test[2])>0.00001) throw Error('Native arithmetic self-test failed: '+test);
// Verify left/center/right round trips before installing any hook.
{
  const fw=new NativeFunction(native.test_forward,'uint32',['uint32']);
  const inv=new NativeFunction(native.test_inverse,'uint32',['uint32']);
  const b=new ArrayBuffer(4),v=new DataView(b),saved=state.readU32();
  const bits=x=>{v.setFloat32(0,x,true);return v.getUint32(0,true);};
  const num=x=>{v.setUint32(0,x,true);return v.getFloat32(0,true);};
  let cases=0,maxError=0;
  for(const scale of [1,0.75,1920/3440,0.4]){
    state.writeU32(Math.round(scale*1048576));
    for(const anchor of [0,0.5,1]){
      const offset=(1048576-state.readU32())*16*anchor;
      state.add(24).writeU32(offset);state.add(28).writeU32(offset);
      for(let i=0;i<=1000;i++){
        const x=num(bits(-0.1+i*0.0012)),f=num(fw(bits(x))),back=num(inv(bits(f)));
        const error=Math.max(Math.abs(f-(x*state.readU32()/1048576+offset/16777216)),Math.abs(back-x));
        if(error>0.000002)throw Error('Native anchored coordinate test failed');
        maxError=Math.max(maxError,error);cases++;
      }
    }
  }
  state.writeU32(saved);state.add(24).writeU32((1048576-saved)*8);state.add(28).writeU32((1048576-saved)*8);
  send({coordinateTests:{passed:true,cases,maxPixelErrorAt3440:maxError*3440}});
}
{
  const ty=new NativeFunction(native.translate_y,'uint32',['uint32','int']);
  const b=new ArrayBuffer(4),v=new DataView(b);
  const bits=x=>{v.setFloat32(0,x,true);return v.getUint32(0,true);};
  const num=x=>{v.setUint32(0,x,true);return v.getFloat32(0,true);};
  let maxError=0;const dy=state.add(64).readS32();
  for(let i=0;i<=1000;i++){
    const y=num(bits(i/1000)),physical=num(ty(bits(y),dy)),back=num(ty(bits(physical),-dy));
    maxError=Math.max(maxError,Math.abs(physical-y-HUD_Y),Math.abs(back-y));
  }
  if(maxError>0.000002)throw Error('HUD vertical coordinate test failed');
  send({verticalTests:{passed:true,cases:1001,maxPixelErrorAt1440:maxError*1440}});
}
const quad = new NativeFunction(at(0x51f460),'void',
  ['pointer','float','float','float','float','float','uint32','pointer','float','float','float','float','uint32'],'thiscall');
const reloadHotkeys=new NativeFunction(at(0x45f420),'int',['pointer'],'thiscall');
const refreshCameraKeys=new NativeFunction(at(0x439e40),'void',['pointer'],'thiscall');
const updateHud=new NativeFunction(native.update_hud,"void",[]);
const updateCamera=new NativeFunction(native.update_camera,"void",[]);
let hotkeysReloaded=false;
Interceptor.attach(at(0x538b60), {
  onEnter(){
    // Native loader runs once on the game's own UI thread, between input frames.
    if(!hotkeysReloaded){
      hotkeysReloaded=true;
      const loaded=reloadHotkeys(at(0x5cbc84))===1,camera=at(0x62be68).readPointer();
      if(loaded && !camera.isNull()){
        const keys=()=>[0xa6,0xae,0xb6,0xbe].map(o=>camera.add(o).readU32());
        const before=keys();refreshCameraKeys(camera);
        send({cameraKeysRefreshed:{before,after:keys()}});
      }
      send({hotkeysReloaded:loaded});
    }
    updateHud();
    updateCamera();
    const game=at(0x6d0818).readPointer();
    {
      const renderer=at(0x6d4024).readPointer(),margin=(1-SCALE_X)/2;
      if(game.isNull() || game.add(0x5c).readU32()!==1){
        quad(renderer,0,0,margin,1,0.01,0xff101817,ptr(0),0,0,1,1,0);
        quad(renderer,1-margin,0,1,1,0.01,0xff101817,ptr(0),0,0,1,1,0);
      }
    }
    state.add(16).writeS32(state.add(16).readS32()+1);
  },
  onLeave(){state.add(16).writeS32(state.add(16).readS32()-1);}
});
Interceptor.attach(at(0x51f460), {onEnter:native.quad_primitive});
Interceptor.attach(at(0x51f370), {onEnter:native.triangle});
Interceptor.attach(at(0x51f2b0), {onEnter:native.primitive});
Interceptor.attach(at(0x53fe90), {onEnter:native.event_enter,onLeave:native.event_leave});
Interceptor.attach(at(0x5581e0), {onEnter:native.hit,onLeave:native.hit_leave});
Interceptor.attach(at(0x5582f0), {onEnter:native.hit_outer_enter,onLeave:native.hit_outer_leave});
Interceptor.attach(at(0x4de140), {onEnter:native.world_enter,onLeave:native.world_leave});
Interceptor.attach(at(0x538f10), {onEnter:native.modal_enter,onLeave:native.modal_leave});
Interceptor.attach(at(0x477c10), {onEnter:native.minimap_point});
Interceptor.attach(at(0x53fda0), {onEnter:native.window_draw_enter,onLeave:native.scope_draw_leave});
Interceptor.attach(at(0x552560), {onEnter:native.cursor_enter,onLeave:native.cursor_leave});
Interceptor.attach(at(0x52d140), {onEnter:native.camera_rect});
const drawHooks=new Set();
for(const vt of [0x5ddd18,0x5dd870,0x5ddd98,0x5de360,0x5de3b0,0x5ce840]){
  const fn=at(vt).add(0x18).readPointer();
  if(!drawHooks.has(fn.toString())){
    drawHooks.add(fn.toString());
    Interceptor.attach(fn,{onEnter:native.control_draw_enter,onLeave:native.scope_draw_leave});
  }
}
const viewportSamples=new Set();
const renderer=at(0x6d4024).readPointer();
const mode=renderer.add(0x34).readPointer().add(renderer.add(0x11421e).readU32()*21);
const screenWidth=mode.readU32(),screenHeight=mode.add(4).readU32();
const savedFullscreen=renderer.add(0x114226).readU8();
// The device is already created at native resolution. dgVoodoo owns a borderless
// window; make the engine use its windowed focus/mouse paths after initialization.
renderer.add(0x114226).writeU8(0);
Interceptor.attach(at(0x548180),{onEnter(args){
  const a=[0,1,2,3].map(i=>args[i].toInt32()),k=JSON.stringify(a);
  if(!viewportSamples.has(k)){viewportSamples.add(k);if(viewportSamples.size<20)send({viewport:a,caller:this.returnAddress.toString()});}
  if(this.returnAddress.equals(at(0x548326)) && a[0]===0 && a[1]===0 && a[2]===screenWidth && a[3]>=screenHeight*0.65 && a[3]<screenHeight*0.8){args[3]=ptr(screenHeight);}
}});
const imports={};
for(const name of ['ShowWindow','SetWindowPos','DefWindowProcA']){
  const f=Process.getModuleByName('user32.dll').getExportByName(name);
  for(let va=0x5c8000;va<0x5c8500;va+=4)if(at(va).readPointer().equals(f))imports[name]='0x'+va.toString(16);
}
send({imports});
rpc.exports={
  restore(){state.add(80).writeU32(1);renderer.add(0x114226).writeU8(savedFullscreen);
    const camera=at(0x62be68).readPointer();
    if(!camera.isNull() && camera.equals(state.add(68).readPointer()) && camera.readPointer().equals(at(0x5ca078))){
      camera.add(0x5c).writeU32(state.add(72).readU32());camera.add(0x64).writeU8(1);camera.add(0x65).writeU8(1);
    }
  },
  inspect(){const out=[];let w=at(0x6d401c).readPointer().readPointer();for(let n=0;!w.isNull()&&n<50;n++,w=w.add(0x58).readPointer()){
    let cs=[],c=w.add(0x70).readPointer();for(let j=0;!c.isNull()&&j<300;j++,c=c.add(0x8e).readPointer())cs.push({id:c.add(4).readU16(),type:c.add(6).readU16(),v:c.readPointer().toString(),rect:[11,15,19,23].map(o=>c.add(o).readFloat())});
    out.push({p:w.toString(),v:w.readPointer().toString(),visible:w.add(0x5c).readU32(),rect:[5,9,13,17].map(o=>w.add(o).readFloat()),controls:cs});
  }const hotkeys=[];for(let key=0;key<256;key++){let p=at(0x6acd78+key*12).readPointer();for(let i=0;!p.isNull()&&i<100;i++,p=p.readPointer())hotkeys.push({key,modifier:p.add(0x94).readU32(),description:p.add(0x10).readCString()});}
  const camera=at(0x62be68).readPointer();
  return {windows:out,hotkeys,rightPanelVisible:state.add(60).readU32(),hudY:HUD_Y,fullscreen:renderer.add(0x114226).readU8(),cameraRect:camera.isNull()?null:[0x50,0x54,0x58,0x5c].map(o=>camera.add(o).readFloat()),cameraUpdates:state.add(76).readU32(),viewports:Array.from(viewportSamples)};},
  stats(){return {scale:SCALE_X,primitives:state.add(8).readU32(),drawDepth:state.add(16).readS32(),inputDepth:state.add(20).readS32(),minimapPoints:state.add(44).readU32(),selftest:test};}
};
send({ready:true,revision:10,menuArtwork:!!menuArt,scale:SCALE_X,hudSplit:HUD_SPLIT,hudY:HUD_Y,autoHideRight:true,fullCameraViewport:true,footer:false,experimental:true,selftest:test});
