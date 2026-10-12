const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('rt3_ultrawide/assets/controls.js','utf8');

function harness(enabled=true) {
  const memory=new Map(), calls=[];
  let callbacks, detached=false;
  class P {
    constructor(n){this.n=Number(n)>>>0;}
    add(n){return new P(this.n+n);}
    equals(p){return this.n===p.n;}
    isNull(){return this.n===0;}
    toString(){return String(this.n);}
    toUInt32(){return this.n;}
    readU8(){return memory.get(this.n)||0;}
    readU32(){return memory.get(this.n)||0;}
    readPointer(){return new P(memory.get(this.n)||0);}
  }
  const state={foreground:42};
  memory.set(0x6d4018,0x1000);memory.set(0x6d401c,0x3000);
  memory.set(0x6d0818,0x5000);memory.set(0x505c,1);
  const ctx=vm.createContext({
    ptr:n=>new P(n),
    Process:{getModuleByName(){return {getExportByName(){return new P(0xdead);}};}},
    NativeFunction:function(address,returns,args,abi){
      if(address.n===0xdead) {assert.equal(abi,'stdcall');return ()=>new P(state.foreground);}
      assert.equal(address.n,0x54f290);assert.equal(abi,'thiscall');
      assert.deepEqual(Array.from(args),['pointer','pointer','uint32','uint32','uint32']);
      return (...args)=>{calls.push(args.map(a=>a instanceof P?a.n:a));return 1;};
    },
    Interceptor:{attach(address,cb){assert.equal(address.n,0x54e3a0);callbacks=cb;return {detach(){detached=true;}};}}
  });
  vm.runInContext(source,ctx);
  const runtime=ctx.createControlsRuntime({at:n=>new P(n),enabled});
  function event(message,button=1,window=42){
    const args=[new P(window),new P(message),new P(button<<16),new P(0)];
    const invocation={};let result=0;
    callbacks.onEnter.call(invocation,args);
    callbacks.onLeave.call(invocation,{replace(n){result=n;}});
    return {message:args[1].n,result};
  }
  return {state,memory,calls,runtime,event,detached:()=>detached};
}

test('side buttons enqueue paired native Escape/Space events on release only',()=>{
  const h=harness();
  assert.deepEqual(h.event(0x20b,1),{message:0,result:1});
  assert.equal(h.calls.length,0);
  h.event(0x20c,1);
  assert.deepEqual(h.calls,[[0x1000,42,0x100,27,0x10001],[0x1000,42,0x101,27,0xc0010001]]);
  h.event(0x20b,2);h.event(0x20c,2);
  assert.deepEqual(h.calls.slice(2),[[0x1000,42,0x100,32,0x390001],[0x1000,42,0x101,32,0xc0390001]]);
  assert.equal(h.runtime.stats().pause,1);
});
test('no orphan releases, cross-window gestures or double-click pause toggles',()=>{
  const h=harness();h.event(0x20c,2);
  h.event(0x20b,2);h.event(0x20b,2);h.event(0x20c,2);
  h.event(0x20d,2);h.event(0x20c,2);assert.equal(h.calls.length,2);
  h.event(0x20b,2);h.state.foreground=43;h.event(0x20c,2,43);assert.equal(h.calls.length,2);
});
test('focus loss discards an armed gesture even after focus returns',()=>{
  for(const message of [8,0x1c]){
    const h=harness();h.event(0x20b);h.event(message,0);
    h.state.foreground=99;h.event(0x20c);h.state.foreground=42;h.event(0x20c);
    assert.equal(h.calls.length,0);
  }
});
test('native UI lock, modifiers, held keys and background focus block shortcuts',()=>{
  for(const [address,value] of [[0x3c60,0x123],[0x1a8c,4],[0x101b,1],[0x6d4018,0],[0x6d401c,0]]){
    const h=harness();h.event(0x20b,1);h.memory.set(address,value);h.event(0x20c,1);
    assert.equal(h.calls.length,0,`${address.toString(16)} should block release`);
  }
  const h=harness();h.state.foreground=99;h.event(0x20b);h.state.foreground=42;h.event(0x20c);
  assert.equal(h.calls.length,0);
});
test('pause blocked outside gameplay or with Space held; Escape can close menus',()=>{
  const h=harness();h.memory.set(0x505c,0);
  h.event(0x20b,2);h.event(0x20c,2);assert.equal(h.calls.length,0);
  h.event(0x20b,1);h.event(0x20c,1);assert.equal(h.calls.length,2);
  h.memory.set(0x505c,1);h.memory.set(0x1020,1);
  h.event(0x20b,2);h.event(0x20c,2);assert.equal(h.calls.length,2);
});
test('other messages unchanged; opt-out creates no hook; restore detaches',()=>{
  const h=harness();assert.deepEqual(h.event(0x20a),{message:0x20a,result:0});
  h.event(0x20b);h.runtime.restore();h.event(0x20c);
  assert.equal(h.calls.length,0);assert.equal(h.detached(),true);
  assert.equal(harness(false).runtime.stats().enabled,false);
});
