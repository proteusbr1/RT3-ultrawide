# Changelog

## 0.4.0 — Unreleased (experimental)

- Add four reimagined museum paintings with 3840 × 1600 exports, antialiased navigation
  controls, frame-synchronized dissolves and repositioned campaign cabinet hit areas.
- Reduce artwork-mode room changes to about 0.55 seconds, retaining the native
  completion callback so navigation unlocks when the dissolve ends.
- Preserve every original movie and offer original-animation mode in the launcher.
- Prevent the campaign museum from forcing a 640 × 480 renderer/window recreation.
- Extend the menu background fix to submenus with anonymous three-panel controls.
- Refuse repeated helper injection into the same game process; an already-active
  helper is recognized using PID plus process creation time.
- Validate all four packed museum textures, bounded decompression and cache paths.

## 0.3.0 — 2026-10-11 (experimental)

- Added five expanded loading panoramas: trestle bridge, penny on a rail,
  locomotive cab, covered station, and freight yard.
- Preserve native random scene selection and draw the loading status/progress
  separately at their original proportions.
- Replace the three-piece loading backgrounds with one continuous full-display
  quad, using per-scene UV bounds and uniform aspect-ratio cropping.
- Validate and replace 36 loading texture payloads alongside the six menu
  payloads, preserving every other archive byte and the first backup baseline.
- Added loading-upgrade, partial-install detection, unknown-texture rejection,
  and all-variant texture checks. The complete suite now has 25 tests.
- Avoid reporting a temporary unavailable renderer as a resolution change;
  keep the existing stop-on-confirmed-size-change protection.

## 0.2.0 — 2026-10-11 (experimental)

- Added an expanded main-menu background with new woodwork and stained glass.
- Draw the menu background across the display with uniform scaling and aspect
  cropping; retain original button positions, sizes, labels, and hit testing.
- Replaced the old split background and Coast to Coast overlay with one composition.
- Validate and back up the game's texture archive, replacing only six known menu
  texture payloads. All other archive bytes are preserved; restore returns the
  entire original archive.
- Added archive-boundary, overlap, preservation, and repeated-install tests.

## 0.1.0 — 2026-10-11 (experimental)

First public package, consolidating development revisions 1–9.

- Borderless native-resolution display and Alt+Tab without minimizing.
- Proportional HUD/menu/cursor rendering and aligned mouse input.
- Split bottom HUD with conditional right information background.
- Removed unused footer and excess background edges.
- WASD camera movement, Space pause/resume, and relocated conflicting bindings.
- Right/bottom anchoring for World Overview, including its input coordinates.
- Full-height logical camera bounds for labels, icons, projection, and visibility.
- Included checksum-verified dgVoodoo 2.87.5; watermark disabled by configuration.
- English documentation, Windows GUI/CLI, backups, restore support, and packaging.

Validated interactively at 3440×1440 on the executable identified in the README.
Broader compatibility is not implied by this initial release.
