# Controls

| Action | Key |
| --- | --- |
| Move camera forward / left / backward / right | W / A / S / D |
| Pause or resume | Space |
| Multiplayer chat | Ctrl+Space |
| Current train whistle | Shift+W |
| Last dialog | Shift+D |
| Ledger game status | Shift+A |
| Station list | Ctrl+F |
| Hide/show bottom interface | Tab (unchanged) |
| Zoom in/out | Shift+Up / Shift+Down (unchanged from the tested defaults) |
| Rotate camera | Shift+Left / Shift+Right (unchanged from the tested defaults) |

The mod changes only the first eight action groups above. Other existing hotkeys
are retained. These are the game's own bindings, not a global Windows keyboard
remapper. Space therefore follows the game's normal handling of text fields and
dialogs. Camera keys are refreshed in both the hotkey table and the camera's
cached bindings; updating only the text file is insufficient for a running game.

The old Pause-key binding is replaced by Space. Mouse controls remain native,
with coordinates converted to match the relocated UI.
