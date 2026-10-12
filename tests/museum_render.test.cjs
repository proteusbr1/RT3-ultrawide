// Contract test for the native UI drawing bridge; does not emulate Direct3D.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');

test('museum uses native UI depth, valid RHW, and restores render state',()=>{
  const mem=new Map(),calls=[],seeks=[];
  class Pointer {
    constructor(n){this.n=n;}
    add(n){return new Pointer(this.n+n);}
    readU32(){return mem.get(this.n)||0;}
    readS32(){return this.readU32();}
    readU8(){return this.readU32();}
    readU16(){return this.readU32();}
    readFloat(){return this.readU32();}
    writeU32(v){mem.set(this.n,v);}
    writeS32(v){this.writeU32(v);}
    writeU8(v){this.writeU32(v);}
    writeFloat(v){this.writeU32(v);}
    readPointer(){return new Pointer(this.readU32());}
    readCString(){return mem.get(this.n);}
    writeByteArray(){}
    isNull(){return !this.n;}
    toString(){return String(this.n);}
  }
  const ptr=n=>new Pointer(n),state=ptr(0x1000000),renderer=ptr(0x2000000);
  let address=0x3000000,z=.0027;
  const context=vm.createContext({ptr,send(){},File:{readAllBytes:()=>({byteLength:4096*2048*4})},
    Process:{getModuleByName:()=>({getExportByName:()=>ptr(0x8000000)})},
    NativeFunction:function(p){
      if(p.n===0x8000000)return (bink,frame,flags)=>{seeks.push({frame,flags});bink.add(12).writeU32(frame);};
      if(p.n===0x54f640)return ()=>z-=.0000001;
      if(p.n===0x543980)return p=>p;
      return ()=>ptr(address+=0x1000);
    }});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../rt3_ultrawide/assets/museum.js'),'utf8'),context);
  renderer.add(0x11423b).writeU32(4096);renderer.add(0x11423f).writeU32(2048);
  renderer.add(0x114227).writeU8(0xa1);
  state.add(16).writeS32(2);state.add(48).writeU32(4);
  const runtime=context.createMuseumRuntime({at:ptr,state,renderer,scale:1440*4/3/3440,
    artwork:{rooms:['A','B','C','D'].map(path=>({path}))},
    quad(...args){
      assert.equal(renderer.add(0x114227).readU8(),0xa0);
      assert.equal(state.add(16).readS32(),0);
      calls.push(args);
    }});
  runtime.prepare();assert.equal(runtime.enabled,true);
  const c=ptr(0x4000000),w=ptr(0x5000000);
  mem.set(0x625830,0x6000000);mem.set(0x6000000,'Loop_A');
  assert.equal(runtime.draw(c,w),1);
  assert.equal(calls.length,3,'room A draws only its painting, exit and next button; no artificial fan');
  for(let i=0;i<calls.length;i++){
    assert.equal(calls[i][12],0x3f800000,'RHW must be 1.0, not zero');
    assert.ok(calls[i][5]>0&&calls[i][5]<.0027,'depth is ahead of the parent window');
    if(i)assert.ok(calls[i][5]<calls[i-1][5],'later layers are nearer');
  }
  assert.equal(renderer.add(0x114227).readU8(),0xa1);
  assert.equal(state.add(16).readS32(),2);assert.equal(state.add(48).readU32(),4);
  assert.equal(runtime.frames,1);
  const normalNext=calls[2];
  const screenAspect=3440/1440;
  assert.ok(Math.abs((normalNext[3]-normalNext[1])*screenAspect-(normalNext[4]-normalNext[2]))<1e-6,'navigation stays square');
  state.add(240).writeFloat((normalNext[1]+normalNext[3])/2);
  state.add(244).writeFloat((normalNext[2]+normalNext[4])/2);
  calls.length=0;runtime.draw(c,w);
  assert.ok(calls[2][8]>normalNext[8],'hover selects the highlighted atlas tile');
  const bink=ptr(0x7000000);c.add(0xf2).writeU32(bink.n);
  bink.add(8).writeU32(105);
  bink.add(20).writeU32(30);bink.add(24).writeU32(1);
  for(const pair of ['A_to_B','B_to_A','B_to_C','C_to_B','C_to_D','D_to_C']){
    mem.set(0x6000000,'Transition_'+pair);
    const before=seeks.length;
    for(const frame of [1,96,105]){
      bink.add(12).writeU32(frame);calls.length=0;runtime.draw(c,w);
      assert.equal(calls.length,2,'transitions have two paintings and no navigation or fan overlay');
      const t=frame===1?0:(frame-88)/17;
      assert.equal(calls[1][6]>>>24,Math.round(t*t*(3-2*t)*255));
      assert.equal(seeks.length,before+1,'seek once per transition, never once per frame');
      assert.equal(seeks.at(-1).frame,88,'only 17 movie frames remain at 30 fps');
    }
  }
  mem.set(0x6000000,'Loop_B');calls.length=0;runtime.draw(c,w);
  assert.equal(calls.length,4,'destination room restores both navigation buttons');
  assert.equal(seeks.length,6,'room loops are never accelerated');
});
