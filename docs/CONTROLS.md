# Controls

## Modern navigation

| Action | Shortcut | Previous binding replaced |
| --- | --- | --- |
| Pan forward / left / backward / right | W / A / S / D | Arrow keys |
| Faster camera panning | Hold Shift with WASD (3x) | See conflict changes below |
| Rotate left / right | Q / E | Shift+Left / Shift+Right |
| Zoom in / out | R / V | Shift+Up / Shift+Down |
| Pause or resume | Space; forward mouse side button during gameplay | Pause |
| Back / cancel | Rear mouse side button, equivalent to Escape | Escape remains available |
| Save dialog | Ctrl+S | F7 |
| Load dialog | Ctrl+O | F8 |
| Quick save | F5 | Shift+F7 |
| Buy station | Ctrl+E | Ctrl+S |
| Traffic density overview | Shift+F5 | F5 |
| Multiplayer chat | Ctrl+Space | Space |
| Current train whistle | Ctrl+W | W |
| Last dialog | Ctrl+D | D |
| Ledger game status | Ctrl+A | A |
| Station list | Ctrl+F | S |
| Station detail | Ctrl+G | Shift+S |

These replace bindings in the game's own hotkey file; they are not additional
keyboard aliases. **F5 invokes the game's quick save and can replace its previous
quick save.** Ctrl+S opens the regular save dialog. Quick load remains Shift+F8.
The installer rejects collisions with unrelated custom bindings.

Holding either Shift accelerates keyboard panning only; release it to return to
normal. It does not change simulation speed, zoom, rotation or mouse-edge panning.
The former Shift+W/A/D shortcuts move to Ctrl+W/A/D, and station detail moves
from Shift+S to Ctrl+G, so fast navigation cannot open these panels.

## Useful original controls retained

| Action | Control |
| --- | --- |
| Zoom | Mouse wheel |
| Rotate camera | Right mouse drag |
| Hide/show HUD | Tab |
| Undo track laying | Ctrl+Z |
| Lay track / buy train | Ctrl+L / Ctrl+T |
| Find city | F |
| Train / company / station lists | T / C / Ctrl+F |
| Next / previous train, company or station | Page Down / Page Up |
| Assign camera bookmark | Shift+0 through Shift+9 |
| Recall camera bookmark | 0 through 9 |
| Speed up / slow down | + / - |

Left click, middle click, right click and the wheel keep their original handling.
The native camera controls are described in the
[RT3 manual](https://cdn.akamai.steamstatic.com/steam/apps/7610/manuals/manual_en.pdf).

## Side-button behavior and preferences

Enable or disable **Mouse side buttons** in the launcher, then restart the game.
The preference is saved locally and also applies to the CMD launcher.
For command-line users, create `<game>/RT3Ultrawide/NATIVE_MOUSE` to disable
shortcuts or remove that marker to enable them on the next launch.

Buttons act on release, once per gesture. A double-click does not toggle pause
twice. Shortcuts require the game window to be foreground, no keyboard modifier,
no held Escape/Space key, and the native hotkey gate to be unlocked.
Losing focus cancels an unfinished gesture. Pause additionally requires gameplay.
Escape follows the current window's normal cancel/back behavior; it does not
provide browser-style navigation history. Locked text/modal contexts retain the
game's normal keyboard behavior instead of receiving a mouse shortcut.

Mouse software must expose standard Back/Forward (XBUTTON1/XBUTTON2) messages.
If it maps those buttons to macros or keys, select standard side buttons in
that software. The mod sends no global Windows keyboard events.

## Design choices and remaining ideas

This first modernization keeps camera commands close to WASD, adds familiar save
shortcuts, and puts cancel/pause under the thumb. It preserves native right-drag,
wheel and track-building behavior, which are already context-sensitive.

Middle-drag panning, a command palette and arbitrary per-button rebinding remain
ideas, not implemented features. They need broader gameplay/editor validation
before replacing context-sensitive original interactions.

Keyboard changes use RT3's native bindings and text/dialog handling. Camera keys
are refreshed in both the hotkey table and the camera's cached bindings. Mouse
shortcuts feed paired key events into the native input queue through a guarded
game-window hook; they never call simulation commands directly. Runtime `stats`
reports enabled state, dispatched counts, blocked messages and any hook error.
