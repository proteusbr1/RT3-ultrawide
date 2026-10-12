# Validation record

Date: 2026-10-11. Development environment: Windows 11 Pro, 3440×1440,
Steam executable SHA-256 listed in the README. Initial development used dgVoodoo
2.87.3; the distributed package and final upgrade checks use 2.87.5.

## Interactive checks

The game owner confirmed these with a physical mouse/keyboard during development:

- WASD moves the camera in all four directions after refreshing the camera cache.
- Briefing and minimap clicks match their visible locations.
- Right train information panel and minimap controls remain responsive.
- HUD sits at the bottom; the right background hides and reappears with information.
- World Overview is correctly positioned at the bottom right and its categories/products respond.
- City names and icons remain visible in the lower map area after the camera-bound fix.

Visual inspection confirmed split HUD placement and removal of the dgVoodoo
watermark in the active session using the official control panel. The on-disk
watermark setting was also verified false.

The packaged installer upgraded the real installation from 2.87.3 to 2.87.5,
backed up the previous DLL/control panel, and preserved the existing settings.
The installed launcher then started a fresh 3440×1440 game with revision 9 active
and all native coordinate checks passing. After loading a saved game, the owner
confirmed that the map/HUD remained correct and the watermark was absent.

Space pause is configured in the native hotkey table; full dialog/text-entry and
multiplayer behavior still needs broader testing. Alt+Tab and borderless behavior
were observed during the development session.

## Automated checks

Version 0.2.0: the generated background was observed in a fresh 3440×1440 game,
covering the complete display with proportional woodwork and glass. Clicking
**Single Player** opened the corresponding submenu at the expected coordinates;
the background remained continuous. The original texture archive was backed up
and all bytes outside the six menu payloads were checked unchanged.

Version 0.3.0: the packaged installer updated the real installation, retaining
the same original archive backup. Every byte outside the 42 menu/loading
payloads was compared with that baseline and remained identical. A fresh
3440×1440 session passed the native coordinate checks with revision 11 and both
artwork paths enabled. After loading a saved game, the owner confirmed that the
loading image filled the display without misplaced fragments and that its
text/progress appeared correctly. All five generated source images were visually
inspected, but every random variant has not been individually captured in-game.

The resolution monitor now distinguishes an unavailable renderer during
transitions/teardown from a confirmed change in width/height. Unavailability is
bounded to ten seconds; valid changed dimensions still stop the helper.

- Native X transforms: 12,012 cases across four scales and three anchors;
  maximum observed error below 0.00124 pixel at width 3440.
- Native Y translation: 1,001 round trips; maximum observed error below
  0.000086 pixel at height 1440.
- Runtime checks the expected code signatures before installing hooks.
- Python tests cover configuration preservation, invalid formats/resolutions,
  hotkey collisions, stable original backups, restore conflicts, corrupt backups,
  rollback after write failure, unsafe manifest paths, unsupported executables,
  and the bundled graphics-wrapper hashes.
- The 25-test suite includes a complete offline install/restore cycle in an
  isolated synthetic fixture, restoration of the startup display flag, an
  upgrade/rollback fixture, and regression coverage for upstream CR-CR-LF config
  line endings so installation does not create duplicate INI sections.
- Menu tests cover payload-only changes, idempotent installation, unknown texture
  rejection, archive bounds/overlap validation, and texture-storage dimensions.
- Loading tests cover all 36 texture levels, preservation of menu/directory and
  unrelated data during upgrades, partial-install detection, original/installed
  state recognition, and rejection of unknown textures.
- The packaged Windows EXE was launched locally; its GUI detected the Steam
  installation and 3440×1440 display, and its diagnostic recognized the expected
  game/wrapper hashes. The packaged launcher attached to the running game,
  passed all native coordinate checks, and remained attached during observation.

## Known limits

### Museum candidate (0.4.0)

- Observed original museum rooms/transitions at 3440 × 1440 with the low-resolution
  mode-switch calls bypassed. The helper stayed attached instead of dropping to
  720 × 480.
- All four new 4096 × 2048 textures uploaded successfully through the native
  texture class in a fresh game process.
- The 30-test suite passes, including all four BGRA payloads, checksum failure,
  bounded decompression, path validation, original-mode opt-out and process reuse.
- The packaged candidate installed successfully, persisted the 3440 × 1440
  launcher configuration and started a fresh game. All four textures uploaded;
  installed JavaScript/metadata matched the source checksums. A repeated Launch
  recognized the active helper without injecting another session.
- The first artwork candidate displayed a black museum. The drawing bridge now
  consumes native UI depths, supplies RHW=1 and preserves native render flags.
  The owner subsequently viewed the artwork and requested removal of the
  procedural fan and replacement of the navigation design. Both are changed.
- `node --test tests/museum_render.test.cjs` checks projection/depth/state,
  square navigation, hover selection, absence of the fan, and the alpha endpoints
  of all six room transitions. It also checks a single seek per transition,
  approximately 0.55 seconds of remaining playback, and untouched room loops.
  Interactive confirmation of the shortened input lock remains pending.
  This does not emulate the graphics driver or the Bink decoder.
- **Pending interactive validation:** actual painting composition in all rooms,
  revised navigation, six dissolves, cabinet selection, medals, exit/re-entry, original-mode
  launch and a gameplay load. This candidate is not yet
  a confirmed public release.
- Source paintings are 1942 × 809; 3840 × 1600 exports are resampled. This does
  not reproduce every animation in the original movies. See
  [museum artwork](MUSEUM_ARTWORK.md).

This initial release is experimental. One game build and one physical resolution
have been exercised interactively. The configurable resolution range is not a
claim that every monitor, DPI setting, GPU, scenario, editor window, multiplayer
flow, or other mod combination has been tested. Long-session stability and a
clean-machine install matrix remain future validation work.

The classic fonts and in-game HUD textures remain unchanged; the menu background
is replaced in 0.2.0 and loading panoramas are added in 0.3.0. The hidden footer removes its
country/hint display, and the collapse widgets are replaced by using Tab. Some
specialized windows may still need their own anchoring classification.

The test suite does not launch the copyrighted game in CI. Automated package
build success is distinct from successful gameplay validation.

## Modern controls (runtime revision 14)

- 31 Python tests and 10 Node tests pass locally. Coverage includes native input
  event pairs, focus loss, UI locks, modifiers, held keys, double-clicks, menu
  pause suppression, opt-out, cleanup and Shift camera-pan scaling.
- The actual installed hotkey file upgrades without conflicts and the
  transformation is idempotent. Existing backup and restore tests also pass.
- WndProc, keyboard bridge, hotkey-gate and camera-pan signatures were checked
  against the supported unpacked executable without attaching a new analysis
  session. The keyboard camera path at 0x43d740 checks UI and foreground focus
  before calling pan at 0x43d130 (return address 0x43dae9).
- The packaged runtime was installed and launched at 3440 x 1440. Revision 14
  reported ready with mouse shortcuts and 3x Shift boost enabled. The running
  native hotkey table contained the new bindings with the expected modifiers.
  A gameplay screenshot confirmed map and split-HUD rendering.
- On 2026-10-11, the user confirmed Q/E rotation, R/V zoom and both mouse side
  buttons. The user also confirmed that Shift with WASD accelerates panning,
  releasing Shift restores normal speed, and no conflicting panels open.
- Save/load/quick-save dialogs, every text-entry context, other mouse drivers,
  editor/multiplayer behavior and prolonged play have not been exhaustively
  tested. Mock tests do not replace those interactive compatibility checks.
