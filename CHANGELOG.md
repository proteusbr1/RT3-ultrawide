# Changelog

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
