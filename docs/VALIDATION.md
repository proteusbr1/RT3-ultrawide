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

- Native X transforms: 12,012 cases across four scales and three anchors;
  maximum observed error below 0.00124 pixel at width 3440.
- Native Y translation: 1,001 round trips; maximum observed error below
  0.000086 pixel at height 1440.
- Runtime checks the expected code signatures before installing hooks.
- Python tests cover configuration preservation, invalid formats/resolutions,
  hotkey collisions, stable original backups, restore conflicts, corrupt backups,
  rollback after write failure, unsafe manifest paths, unsupported executables,
  and the bundled graphics-wrapper hashes.
- The 17-test suite includes a complete offline install/restore cycle in an
  isolated synthetic fixture, restoration of the startup display flag, an
  upgrade/rollback fixture, and regression coverage for upstream CR-CR-LF config
  line endings so installation does not create duplicate INI sections.
- The packaged Windows EXE was launched locally; its GUI detected the Steam
  installation and 3440×1440 display, and its diagnostic recognized the expected
  game/wrapper hashes. The packaged launcher attached to the running game,
  passed all native coordinate checks, and remained attached during observation.

## Known limits

This initial release is experimental. One game build and one physical resolution
have been exercised interactively. The configurable resolution range is not a
claim that every monitor, DPI setting, GPU, scenario, editor window, multiplayer
flow, or other mod combination has been tested. Long-session stability and a
clean-machine install matrix remain future validation work.

The classic fonts and textures remain unchanged. The hidden footer removes its
country/hint display, and the collapse widgets are replaced by using Tab. Some
specialized windows may still need their own anchoring classification.

The test suite does not launch the copyrighted game in CI. Automated package
build success is distinct from successful gameplay validation.
