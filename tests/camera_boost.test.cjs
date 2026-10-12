const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

function setup() {
  const mem=new Map([[0x62be68,0x7000],[0x6d4018,0x1000],[0x6d401c,0x3000],
    [0x6d0818,0x5000],[0x505c,1],[0x1010,1],[0x1057,1],[0x1a8c,2],
    [0x9004,-0.25],[0x9008,0.5]]);
  let callback,detached=false;
  class P {
    constructor(n){this.n=n;}
    add(n){return new P(this.n+n);}
    equals(p){return this.n===p.n;}
    isNull(){return this.n===0;}
    readPointer(){return new P(mem.get(this.n)||0);}
    readU32(){return mem.get(this.n)||0;}
    readU8(){return mem.get(this.n)||0;}
    readFloat(){return mem.get(this.n);}
    writeFloat(v){mem.set(this.n,Math.fround(v));}
  }
  const ctx=vm.createContext({Interceptor:{attach(address,cb){
    assert.equal(address.n,0x43d130);callback=cb;return {detach(){detached=true;}};
  }}});
  vm.runInContext(fs.readFileSync('rt3_ultrawide/assets/controls.js','utf8'),ctx);
  const runtime=ctx.createCameraBoostRuntime({at:n=>new P(n)});
  const invoke=(caller=0x43dae9)=>callback.onEnter.call({
    returnAddress:new P(caller),context:{ecx:new P(0x7000),esp:new P(0x9000)}});
  return {mem,runtime,invoke,detached:()=>detached};
}

test('Shift pan scales signed native deltas exactly 3x without changing other state',()=>{
  const h=setup(), before=new Map(h.mem);h.invoke();
  assert.equal(h.mem.get(0x9004),-0.75);assert.equal(h.mem.get(0x9008),1.5);
  for(const [key,value] of before)if(key!==0x9004&&key!==0x9008)assert.equal(h.mem.get(key),value);
  assert.equal(h.runtime.stats().boostedCalls,1);
  h.mem.set(0x1010,0);h.mem.set(0x9004,-0.25);h.mem.set(0x9008,0.5);h.invoke();
  assert.equal(h.mem.get(0x9004),-0.25);assert.equal(h.mem.get(0x9008),0.5);
});

test('all four direction keys allow boost; Ctrl/Alt, menus and UI locks do not',()=>{
  for(const key of [87,65,83,68]){
    const h=setup();h.mem.set(0x1057,0);h.mem.set(0x1000+key,1);h.invoke();
    assert.equal(h.runtime.stats().boostedCalls,1);
  }
  for(const [key,value] of [[0x1010,0],[0x1057,0],[0x1a8c,6],[0x1a8c,34],
    [0x505c,0],[0x3c60,0x123],[0x6d4018,0],[0x6d401c,0],[0x6d0818,0],[0x62be68,0]]){
    const h=setup();h.mem.set(key,value);h.invoke();
    assert.equal(h.mem.get(0x9004),-0.25);assert.equal(h.runtime.stats().boostedCalls,0);
  }
});

test('other camera callers, invalid deltas and restored runtime remain untouched',()=>{
  const h=setup();h.invoke(0x43b123);assert.equal(h.mem.get(0x9004),-0.25);
  h.mem.set(0x9008,NaN);h.invoke();assert.equal(h.mem.get(0x9004),-0.25);
  h.mem.set(0x9008,0.5);h.runtime.restore();h.invoke();
  assert.equal(h.mem.get(0x9004),-0.25);assert.equal(h.detached(),true);
});
