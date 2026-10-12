'use strict';
// Optional museum plates. Original Bink playback continues to drive room changes,
// timing, callbacks, campaign progression and sound; only its quad is replaced.
function createMuseumRuntime({at, quad, state, renderer, scale, artwork}) {
  const api={enabled:false,frames:0,room:null,transition:null,error:null};
  if(!artwork)return Object.assign(api,{prepare(){},draw(){return 0;},restore(){}});
  const allocate=new NativeFunction(at(0x53b070),'pointer',['uint32'],'mscdecl');
  const malloc=new NativeFunction(at(0x5a125d),'pointer',['uint32'],'mscdecl');
  const construct=new NativeFunction(at(0x543980),'pointer',['pointer','pointer','uint32','uint32','int'],'thiscall');
  const nextDepth=new NativeFunction(at(0x54f640),'float',[],'mscdecl');
  const seekMovie=new NativeFunction(Process.getModuleByName('binkw32.dll').getExportByName('_BinkGoto@12'),
    'void',['pointer','uint32','int'],'stdcall');
  const textures=[],layouts=new Map();
  let activeTransition=null;
  let navigationTexture=null;
  const artAspect=3840/1600,displayAspect=(4/3)/scale,artWidth=artAspect/displayAspect;
  const artLeft=(1-artWidth)/2;
  const toLogical=x=>0.5+(x-0.5)*artAspect/(4/3);
  // Normalized painting bounds, independently measured for every cabinet.
  const cases=[
    [.210,.600,.324,.954],[.334,.563,.417,.930],[.423,.499,.524,.934],[.528,.562,.644,.939],[.656,.545,.790,.982],
    [.206,.491,.331,.884],[.332,.457,.437,.882],[.438,.433,.551,.894],[.551,.441,.660,.884],[.661,.480,.790,.916],
    [.337,.511,.454,.913],[.512,.495,.613,.882],[.646,.439,.770,.938],
    [.331,.480,.424,.995],[.440,.494,.539,.995],[.551,.480,.644,.995]
  ];
  const roomRanges=[[0,5],[5,10],[10,13],[13,16]];
  const navRects=new Map();
  // Square controls measured in screen-height units, anchored to screen edges.
  const logicalX=x=>(x-(1-scale)/2)/scale,buttonH=.046,buttonW=buttonH*.75;
  for(const id of [50019,50021,50023])navRects.set(id,[logicalX(.024),.918,buttonW,buttonH]);
  for(const id of [50018,50020,50022])navRects.set(id,[logicalX(.976)-buttonW,.918,buttonW,buttonH]);
  for(const id of [50067,50068,50069,50070])navRects.set(id,[logicalX(.024),.035,buttonW,buttonH]);
  // Remove the invisible fan interaction as well as the rejected animation.
  navRects.set(50075,[0,0,0,0]);
  navRects.set(50066,[.13,.941,.74,.05]);
  function setLayout(w){
    const key=w.toString();if(layouts.has(key))return;
    const saved=[];let c=w.add(0x70).readPointer();
    for(let n=0;!c.isNull()&&n<256;n++,c=c.add(0x8e).readPointer()){
      const id=c.add(4).readU16();let rect=navRects.get(id);
      if(id>=50002&&id<=50017){const r=cases[id-50002];rect=[toLogical(r[0]),r[1],(r[2]-r[0])*1.8,r[3]-r[1]];}
      if(id>=50050&&id<=50065){const r=cases[id-50050];rect=[toLogical(r[2]-.038),r[1]+.028,c.add(19).readFloat(),c.add(23).readFloat()];}
      if(rect){saved.push({c,id,rect:[11,15,19,23].map(o=>c.add(o).readFloat())});rect.forEach((v,i)=>c.add(11+i*4).writeFloat(v));}
    }
    layouts.set(key,{w,saved});
  }
  function rect(x,y,w,h,color){
    quad(renderer,x,y,x+w,y+h,nextDepth(),color>>>0,ptr(0),0,0,1,1,0x3f800000);
  }
  function logicalRect(x,y,w,h,color){rect((1-scale)/2+x*scale,y,w*scale,h,color);}
  function picture(room,alpha){
    const color=((Math.round(alpha*255)<<24)|0xffffff)>>>0;
    // Match the native movie quad: consume a UI depth and use RHW=1. A fixed
    // depth can put the plate behind the window; RHW=0 is not a valid UI vertex.
    quad(renderer,artLeft,0,artLeft+artWidth,1,nextDepth(),color,textures[room],0,0,3840/4096,1600/2048,0x3f800000);
  }
  function upload(bytes,width,height){
    const pixels=malloc(bytes.byteLength),object=allocate(0xec);
    if(pixels.isNull()||object.isNull())throw Error('Museum texture allocation failed');
    pixels.writeByteArray(bytes);
    return construct(object,pixels,width,height,1);
  }
  // Rasterize code-defined vector controls once, with analytic antialiasing.
  // The texture atlas avoids hundreds of jagged rectangle primitives per frame.
  function navigationAtlas(){
    const width=1024,height=128,pixels=new Uint8Array(width*height*4);
    const clamp=v=>Math.max(0,Math.min(1,v));
    function distance(x,y,a,b){
      const dx=b[0]-a[0],dy=b[1]-a[1],t=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy));
      return Math.hypot(x-a[0]-dx*t,y-a[1]-dy*t);
    }
    for(let tile=0;tile<6;tile++){
      const kind=tile%3,hover=tile>=3;
      const lines=kind===2?[[[.35,.35],[.65,.65]],[[.65,.35],[.35,.65]]]:
        kind===0?[[[.58,.29],[.38,.50]],[[.38,.50],[.58,.71]]]:
        [[[.42,.29],[.62,.50]],[[.62,.50],[.42,.71]]];
      for(let y=0;y<128;y++)for(let x=0;x<128;x++){
        const qx=Math.abs(x+.5-64)-47,qy=Math.abs(y+.5-64)-47;
        const edge=Math.hypot(Math.max(qx,0),Math.max(qy,0))+Math.min(Math.max(qx,qy),0)-12;
        const coverage=clamp(.5-edge),border=clamp(1.8-Math.abs(edge+1.4));
        const glyph=clamp((.013-Math.min(...lines.map(([a,b])=>distance((x+.5)/128,(y+.5)/128,a,b))))*128+.5);
        const background=hover?[39,43,37]:[18,23,23],gold=hover?[244,224,178]:[201,177,128];
        const ink=Math.max(border*.65,glyph),index=(y*width+tile*128+x)*4;
        const rgb=background.map((v,i)=>Math.round(v+(gold[i]-v)*ink));
        pixels[index]=rgb[2];pixels[index+1]=rgb[1];pixels[index+2]=rgb[0];
        pixels[index+3]=Math.round(coverage*(hover?244:216));
      }
    }
    return pixels.buffer;
  }
  function button(id,direction){
    const [x,y,w,h]=navRects.get(id),left=(1-scale)/2+x*scale;
    const mx=state.add(240).readFloat(),my=state.add(244).readFloat();
    const hover=mx>=left&&mx<=left+w*scale&&my>=y&&my<=y+h;
    const tile=(direction<0?0:direction>0?1:2)+(hover?3:0);
    quad(renderer,left,y,left+w*scale,y+h,nextDepth(),0xffffffff,navigationTexture,
      (tile*128+.5)/1024,.5/128,((tile+1)*128-.5)/1024,127.5/128,0x3f800000);
  }
  function navigation(room){
    button(50067+room,0);
    if(room>0)button(room===1?50019:room===2?50021:50023,-1);
    if(room<3)button(room===0?50018:room===1?50020:50022,1);
    const mx=(state.add(240).readFloat()-artLeft)/artWidth,my=state.add(244).readFloat();
    for(let n=roomRanges[room][0];n<roomRanges[room][1];n++){
      const r=cases[n];if(mx<r[0]||mx>r[2]||my<r[1]||my>r[3])continue;
      logicalRect(.13,.941,.74,.05,0xa00d1715);
      // Restrained corner brackets identify the hovered cabinet, not a giant box.
      const x=artLeft+r[0]*artWidth,w=(r[2]-r[0])*artWidth,y=r[1],h=r[3]-r[1];
      for(const [xx,yy,sx,sy] of [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){
        rect(xx+(sx<0?-.009:0),yy,.009,.0015,0xffdfc68e);rect(xx,yy+(sy<0?-.018:0),.0007,.018,0xffdfc68e);
      }
    }
  }
  let attempted=false;
  api.newWindow=function(w){layouts.delete(w.toString());};
  api.prepare=function(){
    if(attempted)return;attempted=true;
    try{
      if(renderer.add(0x11423b).readU32()<4096||renderer.add(0x11423f).readU32()<2048)throw Error('4096x2048 textures unavailable');
      for(const room of artwork.rooms){
        const bytes=File.readAllBytes(room.path);
        if(bytes.byteLength!==4096*2048*4)throw Error('Unexpected museum texture length');
        // The native texture takes ownership of this CRT-allocated pixel buffer.
        textures.push(upload(bytes,4096,2048));
      }
      navigationTexture=upload(navigationAtlas(),1024,128);
      api.enabled=true;state.add(120).writeU32(1);
      send({museumArtwork:{ready:true,rooms:4,export:[3840,1600],source:artwork.rooms[0].source_size}});
    }catch(error){api.error=String(error);send({museumArtwork:{ready:false,error:api.error,usingOriginalMovies:true}});}
  };
  api.draw=function(c,w){
    if(!api.enabled)return 0;
    const id=c.add(0xea).readU32();if(id>=100)return 0;
    const p=at(0x625830+id*16).readPointer();if(p.isNull())return 0;
    const name=p.readCString(),loop=/^Loop_([A-D])$/.exec(name),transition=/^Transition_([A-D])_to_([A-D])$/.exec(name);
    if(!loop&&!transition)return 0;
    setLayout(w);
    const depth=state.add(16).readS32(),skin=state.add(48).readU32();state.add(16).writeS32(0);
    const flags=renderer.add(0x114227),savedFlags=flags.readU8();
    flags.writeU8(savedFlags&0xf0); // The same draw state used by native Bink UI.
    try{
      if(loop){activeTransition=null;const room=loop[1].charCodeAt(0)-65;picture(room,1);navigation(room);api.room=loop[1];api.transition=null;}
      else{
        const bink=c.add(0xf2).readPointer();let t=0;
        if(!bink.isNull()){
          const key=c.toString()+':'+bink.toString()+':'+name,frames=bink.add(8).readU32();
          if(!activeTransition||activeTransition.key!==key){
            // Keep 0.55 seconds of the existing movie clock. Seeking once lets
            // native playback reach its own completion callback and unlock UI.
            // Merely speeding the dissolve leaves invisible multi-second input lag.
            const numerator=bink.add(20).readU32(),denominator=bink.add(24).readU32();
            const fps=numerator>0&&denominator>0?numerator/denominator:30;
            const remaining=Math.max(1,Math.round(Math.min(240,Math.max(1,fps))*.55));
            const start=Math.max(1,frames-remaining);
            if(start>1)seekMovie(bink,start,0);
            activeTransition={key,start};
          }
          t=(bink.add(12).readU32()-activeTransition.start)/Math.max(1,frames-activeTransition.start);
        }
        t=Math.max(0,Math.min(1,t));t=t*t*(3-2*t);
        picture(transition[1].charCodeAt(0)-65,1);picture(transition[2].charCodeAt(0)-65,t);
        api.transition=name;
      }
      api.frames++;
    }finally{flags.writeU8(savedFlags);state.add(16).writeS32(depth);state.add(48).writeU32(skin);}
    return 1;
  };
  api.restore=function(){
    api.enabled=false;state.add(120).writeU32(0);
    let w=at(0x6d401c).readPointer().readPointer();
    for(let n=0;!w.isNull()&&n<50;n++,w=w.add(0x58).readPointer()){
      const layout=layouts.get(w.toString());if(!layout||!w.readPointer().equals(at(0x5d0570)))continue;
      for(const item of layout.saved)if(item.c.add(4).readU16()===item.id)item.rect.forEach((v,i)=>item.c.add(11+i*4).writeFloat(v));
    }
    // Engine-owned textures remain valid until process exit, including queued
    // draw commands. A clean detach never frees a texture still used by RT3.
  };
  return api;
}
