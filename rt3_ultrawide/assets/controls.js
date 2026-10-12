'use strict';

// Pure gesture policy, shared by the native adapter and its regression tests.
function createMouseGesturePolicy() {
  const armed = new Map();
  return {
    clear() { armed.clear(); },
    event(message, button, window, allowed) {
      if (message === 8 || (message === 0x1c && !allowed)) {
        armed.clear();
        return null;
      }
      if (button !== 1 && button !== 2) return null;
      if (message === 0x20b) {
        if (allowed && !armed.has(button)) armed.set(button, window);
        else if (!allowed) armed.delete(button);
      } else if (message === 0x20d) {
        // A double-click is still one deliberate gesture, not two pause toggles.
        armed.delete(button);
      } else if (message === 0x20c) {
        const matched = armed.get(button) === window;
        armed.delete(button);
        if (matched && allowed) return button === 1 ? 27 : 32;
      }
      return null;
    }
  };
}

// Scale only the two pan arguments produced by the native keyboard camera path.
// That caller already checks the UI lock, frame interval and foreground window.
// No simulation clock, camera coordinates or global speed settings are changed.
function createCameraBoostRuntime({at}) {
  const report={enabled:true,multiplier:3,boostedCalls:0,error:null};
  const hook=Interceptor.attach(at(0x43d130), {
    onEnter() {
      try {
        if (!report.enabled || !this.returnAddress.equals(at(0x43dae9))) return;
        const camera=at(0x62be68).readPointer();
        if (camera.isNull() || !camera.equals(this.context.ecx)) return;
        const input=at(0x6d4018).readPointer(), ui=at(0x6d401c).readPointer();
        const game=at(0x6d0818).readPointer();
        if (input.isNull() || ui.isNull() || game.isNull()) return;
        if (game.add(0x5c).readU32()!==1 || !ui.add(0xc60).readPointer().isNull()) return;
        if (!input.add(0x10).readU8() || (input.add(0xa8c).readU32() & ~3)!==0) return;
        if (![87,65,83,68].some(key=>input.add(key).readU8()!==0)) return;
        // x86 thiscall: ECX is the camera, the two float arguments follow RET.
        const x=this.context.esp.add(4), y=this.context.esp.add(8);
        const dx=x.readFloat(), dy=y.readFloat();
        if (!Number.isFinite(dx) || !Number.isFinite(dy)) return;
        x.writeFloat(dx*report.multiplier);y.writeFloat(dy*report.multiplier);
        report.boostedCalls++;
      } catch(error) { report.error=String(error);report.enabled=false; }
    }
  });
  return {stats:()=>({...report}),restore(){report.enabled=false;hook.detach();}};
}

function createControlsRuntime({at, enabled}) {
  const report = {enabled:!!enabled, back:0, pause:0, blocked:0, error:null};
  if (!enabled) return {stats:()=>({...report}), restore(){}};
  const policy = createMouseGesturePolicy();
  const foreground = new NativeFunction(
    Process.getModuleByName('user32.dll').getExportByName('GetForegroundWindow'),
    'pointer', [], 'stdcall');
  // Feed the normal game input queue, keeping its UI/hotkey dispatch in charge.
  const keyboard = new NativeFunction(at(0x54f290), 'int',
    ['pointer','pointer','uint32','uint32','uint32'], 'thiscall');

  function context(hwnd, button) {
    if (!report.enabled || !foreground().equals(hwnd)) return null;
    const input=at(0x6d4018).readPointer(), ui=at(0x6d401c).readPointer();
    if (input.isNull() || ui.isNull()) return null;
    // The same gate used by the game's native hotkey dispatcher.
    if (!ui.add(0xc60).readPointer().isNull() || input.add(0xa8c).readU32() !== 0) return null;
    const key=button===1?27:32;
    if (input.add(key).readU8() !== 0) return null;
    if (button===2) {
      const game=at(0x6d0818).readPointer();
      if (game.isNull() || game.add(0x5c).readU32() !== 1) return null;
    }
    return input;
  }

  const hook=Interceptor.attach(at(0x54e3a0), {
    onEnter(args) {
      this.sideButton=false;
      try {
        const hwnd=args[0], message=args[1].toUInt32(), wp=args[2].toUInt32();
        if (message===8 || (message===0x1c && wp===0)) policy.clear();
        if (message!==0x20b && message!==0x20c && message!==0x20d) return;
        const button=(wp>>>16)&0xffff;
        if (button!==1 && button!==2) return;
        const input=context(hwnd,button);
        this.key=policy.event(message,button,hwnd.toString(),!!input);
        this.hwnd=hwnd;
        this.button=button;
        this.sideButton=true;
        // Native RT3 has no XBUTTON handler. Mark our message handled.
        args[1]=ptr(0); // WM_NULL; do not let DefWindowProc process XBUTTON again.
        if (!input) report.blocked++;
      } catch(error) {
        report.error=String(error); policy.clear(); report.enabled=false;
      }
    },
    onLeave(result) {
      if (!this.sideButton) return;
      result.replace(1);
      if (!this.key) return;
      try {
        const input=context(this.hwnd,this.button);
        if (!input) { report.blocked++; return; }
        const scan=this.key===27?0x01:0x39;
        keyboard(input,this.hwnd,0x100,this.key,(scan<<16)|1);
        keyboard(input,this.hwnd,0x101,this.key,(0xc0000001|(scan<<16))>>>0);
        report[this.key===27?'back':'pause']++;
      } catch(error) {
        report.error=String(error); policy.clear(); report.enabled=false;
      }
    }
  });
  return {stats:()=>({...report}), restore(){report.enabled=false;policy.clear();hook.detach();}};
}
