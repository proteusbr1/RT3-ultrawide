# Reimagined campaign museum

The campaign museum has four new illustrated rooms, based on the four original
`Loop_A` through `Loop_D` scenes. The room identities, cabinet counts and order
remain recognizable. The native campaign buttons, progression and selection
callbacks are retained; cabinet hit areas are repositioned for the new paintings.

| Room | Subject | Campaign cabinets |
| --- | --- | --- |
| A | Stagecoach and early steam engine | 5 |
| B | Mallard and the grand station clock | 5 |
| C | Red locomotive and international exhibits | 3 |
| D | Globe, early machinery and bell jars | 3 |

## Resolution and animation

The generated source PNGs are **1942 × 809**. They are resampled to **3840 × 1600**
and packed into 4096 × 2048 BGRA textures. This is a 4K-width export, **not native
4K generated detail**. Uniform scaling fills a 3440 × 1440 display without
stretching. Narrower displays crop peripheral architecture; wider displays can
retain side margins rather than crop the cabinets vertically.

This is an image-based reinterpretation, not remastered video. The rejected procedural
fan has been removed, including its invisible click target. Room changes use a
smooth dissolve synchronized with
the original transition clip's frame counter. The original Bink player still
controls timing, callbacks and sound. Other movements baked into the old videos
(including rotating exhibits/globe) are not recreated in this artwork mode.

**No original `.bik` file is changed or redistributed.** To use all original
animations, uncheck **Reimagined museum artwork** in the launcher, then restart
RT3 with **Launch**. The native-resolution crash fix applies in both modes.
The preference is stored as the presence/absence of
`<game>/RT3Ultrawide/ORIGINAL_MUSEUM`.

## Navigation

Small square controls sit near the display edges, with antialiased brass
chevrons, rounded translucent backgrounds and a brighter mouse-hover state.
The visible bounds and native click rectangles use the same layout. The close
control uses the same design. A code-generated 1024 x 128 texture atlas replaces
the old staircase of rectangle primitives; the original callbacks are retained.

The original transition footage is not spliced between the new paintings: its
architecture and camera composition differ, which would create visible jumps.
Artwork mode seeks each transition clip once to its final approximately 0.55
seconds and maps the dissolve to those remaining frames. The native completion
callback still unlocks the destination controls; there is no invisible wait for
the full 3-3.6 second clip. Earlier audio in that transition clip is skipped.
Room loops, standalone videos and original-video mode retain their timing. Original-video mode still uses the original
animated transitions.

## Sources and reproducible export

- Paintings: `rt3_ultrawide/assets/museum-a.png` through `museum-d.png`.
- Tool: built-in `image_gen`, using locally extracted frames as scene references.
- Exact prompts: [`museum-prompts.json`](../rt3_ultrawide/assets/museum-prompts.json).
- Exporter: [`tools/build_museum_assets.py`](../tools/build_museum_assets.py).
- Metadata/checksums: `rt3_ultrawide/assets/museum-artwork.json`.
- Runtime drawing and cabinet mapping: `rt3_ultrawide/assets/museum.js`.

Run the exporter with Pillow installed in the development environment. The
runtime itself does not need Pillow: it checks SHA-256, decompresses the packed
textures into a validated local cache, and uploads pixels through RT3's own
texture class on the game's UI thread. Four decoded textures use 128 MiB of
pixel storage, plus graphics-driver storage. Hardware must support 4096 × 2048
textures; otherwise the original movies are used and the reason is logged.

The cache lives in `<game>/RT3Ultrawide/museum-cache`. Texture objects stay owned
by the game until process exit, avoiding dangling references in queued drawing
commands after a helper stop. Restart the game to unload them.

## Why the old museum broke the patch

The campaign constructor calls the renderer's resolution routine with 640 × 480.
On the tested system the engine selected 720 × 480 and recreated the window;
the helper then detached because UI coordinates no longer matched its original
3440 × 1440 assumptions.

The runtime now validates and replaces **only two museum CALL instructions**
(entry `0x4b8e8d`, exit `0x4b8de1`) with `add esp, 16; nop; nop`, matching the
callee's stack cleanup. Neither caller uses the return value. The original bytes
are retained and restored on clean detach. `RT3.exe` on disk is untouched.
The original movie control is also fitted proportionally to the native height.

Repeated attachment to an already-used RT3 process can crash the old engine.
The launcher now records the PID **and Windows process creation time**, refuses
a second attachment in that process lifetime, and recognizes an already-active
helper. Close RT3 and launch a fresh process after stopping a helper.

## Validation status

Asset integrity, decompression limits, metadata/path validation, opt-out and
session-reuse tests are automated. Runtime validation must additionally cover
all four rooms, both directions of each transition, cabinet selection, exit and
re-entry, original-animation mode, and a gameplay load. See
[`VALIDATION.md`](VALIDATION.md) for the observed results and remaining limits.
