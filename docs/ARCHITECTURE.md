# Architecture and reverse-engineering notes

## Boundaries

This is a narrowly versioned runtime patch for a 32-bit executable loaded at
`0x400000`. It does not replace the game, modify saves, unpack and redistribute
assets, or alter the game executable on disk. Fixed addresses are accepted only
after the executable hash and function signatures match.

The Python layer handles installation, startup, and one Frida session. The
JavaScript asset installs native hooks through Frida's `CModule`. Most hot-path
coordinate transforms run in native code. The HUD texture split uses a scoped
callback to reuse the game's own draw primitive and original texture coordinates.

Version 0.2.0 also replaces six validated menu texture payloads in the local
2D archive. Full-file backup and restore cover this on-disk change. The generated
background has its own drawing path in Setup window control 3022, while the
interactive menu retains the existing coordinate transform. See
[menu artwork](MENU_ARTWORK.md) for the archive format, rendering, and provenance.

## Coordinate spaces

The original UI assumes a 4:3 coordinate canvas. For display width `W`, height
`H`, and horizontal scale `s = (H × 4/3) / W`:

```text
physical_x = logical_x × s + anchor
anchor = 0            for the left HUD
anchor = (1 - s) / 2  for centered menus
anchor = 1 - s        for right information windows
```

The lower HUD is cropped at original normalized Y `0.954` and translated down by
`0.046`. Input uses the inverse translation and inverse X transform. World input
and cursor hotspots remain in physical screen coordinates.

Scoped state is essential: modal dialogs can run nested event loops, and the
minimap polls raw mouse coordinates independently of ordinary window events.
Applying the inverse transform twice causes offset clicks. Drawing hooks save
and restore their anchor, Y offset, skin type, and nesting depth per invocation.

Integer-only IEEE-754 conversion with 24-bit fixed-point arithmetic avoids the
target's x87 state. Floating-point CModule experiments produced incorrect results
in this process. Native X and Y round-trip tests run before any hook is installed.

## World viewport versus logical camera

Changing the rendering device's viewport alone draws terrain into the old HUD
strip, but leaves the camera's normalized rectangle at `[0, 0, 1, 0.7]`. Other
systems still use that rectangle for visibility, labels, and picking.

Revision 9 updates the **main game camera only**, retaining its previous requested
bottom coordinate for restoration. Its viewport setter is intercepted so that
HUD toggles do not restore the old 70% bound. Camera dirty flags are set so cached
projection/visibility state is refreshed. The device viewport and logical camera
then both cover the complete screen. Auxiliary cameras are not expanded.

## Important addresses in the supported image

These are virtual addresses, not offsets into the on-disk packed executable.

| Address | Role |
| --- | --- |
| `0x538b60` | UI frame, anchor scope, safe hotkey refresh |
| `0x53fda0` | Window drawing scope |
| `0x51f460`, `0x51f370`, `0x51f2b0` | Quad, triangle, and clipping primitives |
| `0x53fe90` | Window input event scope |
| `0x5581e0`, `0x5582f0` | Control hit testing |
| `0x4de140` | World input; restore physical coordinates |
| `0x538f10` | Nested modal input scope |
| `0x477c10`, caller `0x478d12` | Minimap raw-mouse coordinate path |
| `0x552560`, caller `0x53f633` | Native cursor drawing |
| `0x548180`, caller `0x548326` | Rendering viewport setup |
| `0x52d140` | Camera normalized-rectangle setter |
| `0x62be68` | Main camera pointer; rectangle at `+0x50` through `+0x5c` |
| `0x5ca078` | Main game camera vtable |
| `0x5d1990`, `0x5d13b4` | Train Detail and World Overview window vtables |
| `0x6d4024` | Renderer pointer; display/focus flag at `+0x114226` |
| `0x45f420` | Native hotkey loader |
| `0x439e40` | Refresh camera's cached movement keys |

The full-screen display flag is required while creating the native-resolution
device. dgVoodoo creates a borderless window; after initialization, the runtime
switches the engine's focus/input flag to its windowed path. The launcher resets
the startup flag because RT3 can persist the runtime value on exit.

## Installation and recovery

Configuration changes are prepared and validated before writes. The first
baseline is retained in local backups with checksums. A manifest is written
before applying changes, each write is read back, and ordinary write failures
roll back completed writes. The manifest marks an incomplete interrupted install.
Restoration validates backups and preserves current files before replacing them.

The runtime uses an exclusive lock and checks the attached executable's actual
path. It does not attach a second diagnostic session. To inspect a running public
helper, create `<game>/RT3Ultrawide/INSPECT`; it writes `layout.json` through its
existing session. Create `STOP` in that directory for a clean detach.

## Extending support

For a different build, obtain evidence from a legally installed local copy and
map all relevant functions, signatures, structure layouts, and window vtables.
Never remove the hash check as a substitute for that work. Validate both visual
placement and physical mouse input, especially nested dialogs and the minimap.
Keep full memory images and game assets out of this repository.
