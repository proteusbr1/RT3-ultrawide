# Expanded menu artwork

Version 0.2.0 adds a continuous ultrawide wood-and-stained-glass background.
The extra side architecture is newly drawn, rather than a horizontal stretch of
the original 4:3 artwork. The original button graphics, labels, mouse coordinates,
and menu actions are still rendered by the game.

## Files and rendering

- `rt3_ultrawide/assets/menu-background.png`: final generated artwork, 1938×811.
- `menu-background.pk4`: six generated DXT5 texture levels, using the original
  texture names and fixed payload sizes.
- `menu-background.json`: archive checksum, visible image bounds, texture size.
- `tools/build_menu_assets.py`: reproducible encoding step with Pillow 12.3.0.

The image is uniformly scaled to cover the display; UV cropping accounts for
aspect differences. No horizontal-only scaling is applied. The composition was
visually tested at 3440×1440. Other aspect ratios crop the sides or bottom and
still require visual validation, especially the header clearance on 32:9.

The 2048×1024 DDS storage includes padding outside the visible image rectangle.
The runtime excludes that padding from sampling. The texture archive shipped
with the mod contains generated pixels only. Installation validates the six
original texture hashes in the player's `Data/2D/rt3_2DDS.PK4`, backs up that
entire file, and replaces those six same-size payloads. The directory and all
unrelated bytes remain unchanged. Repeated installation is idempotent.

The supported executable's Setup window has vtable `0x5d1664`. Control 3022 draws
the new full-display quad; controls 3023/3024 (old lower fragments) and 3422 (old
Coast to Coast overlay) are hidden only during drawing. Original visibility bits
are restored afterward. Menu controls retain their established input transform.

Start through the ultrawide launcher. A regular Steam launch does not apply this
background layout correction. **Restore original** also restores the texture
archive. Unknown menu replacements are rejected instead of overwritten.

## Provenance and prompts

Created on 2026-10-11 using OpenAI's built-in ImageGen tool, in two editing passes.
The original `Setup_Background_A.dds` was decoded locally to PNG as a visual
reference. It is not distributed. The requested 3440×1440 dimensions were a
generation target; the actual returned final image is 1938×811 and is scaled
uniformly by the renderer. No claim of native 3440×1440 source pixels is made.

Initial prompt:

> Create a production-ready ultrawide background artwork for the Railroad Tycoon 3 main menu, at 3440x1440 (43:18) landscape. The input is the ORIGINAL TEXTURE ATLAS, not a finished screen: the first 1600x1024 pixels show the main section; the narrow rotated strips on its right are the missing bottom of the original 1600x1200 panel. Ignore the white unused atlas areas and do NOT reproduce the atlas arrangement. Reconstruct a continuous full-screen background, then EXPAND THE ART HORIZONTALLY with newly painted matching detail, DO NOT horizontally stretch it. Preserve the original central 4:3 composition at correct proportions occupying the centered 1920x1440 area: embossed gold 'RAILROAD TYCOON 3' logo at the very top center, copper train wheel roundels flanking the logo, ornate warm brown walnut wood, tall leaded stained-glass panels with pale blue sky and muted green lower panes, star and fleur-de-lis medallions. Extend this architecture naturally into the additional 760 pixels on EACH side, with complementary carved wood moldings and more stained glass / subtle blue-green scenic glass detail. Keep the original classic late-Victorian railroad aesthetic, texture, warm brown wood and cool glass color balance. Excellent refined painted game UI art, crisp bevels and consistent lighting, seamless edges, no blur. Maintain a QUIET EMPTY WOODEN CENTRAL COLUMN from x approximately 1400 to 2040 and y 350 to 1390, where real interactive buttons will be drawn by the game. DO NOT draw any buttons, menu labels, Coast to Coast badge, UI controls, extra writing, watermarks, black borders or white areas. Logo must remain centered and proportional, within the top 230 pixels. All side artwork must have correct natural proportions. This is an expanded background only, not a screenshot or device mockup.

Final header refinement prompt:

> Edit this game-menu BACKGROUND with one narrowly targeted header correction. Keep the exact ultrawide canvas aspect ratio, all the wooden architecture, side panels, stained glass, round copper wheels, lighting and blank central button area unchanged. Only revise the CENTRAL LOGO group at the top. Reduce the complete gold 'RAILROAD TYCOON 3' logo uniformly to about 72% of its current width and height, anchored at the same top-center, with all letters and numeral intact. Directly below it add a small elegant dark teal and antique gold railroad nameplate with the exact text 'COAST TO COAST', matching the original game's vintage embossed lettering. Both the main logo and this new subtitle combined must fit entirely within the TOP 25% of the image, with the bottom of the subtitle at about 24% image height. Leave ALL central area below 26% of height as empty wood for the real game buttons. No buttons, no extra labels, no watermark, no black borders. Do not widen, stretch, move or repaint the side stained glass and wood composition. Preserve this as one continuous finished ultrawide background, not an atlas. Output at 3440x1440 if available, otherwise retain the input aspect ratio precisely.

See [third-party notices](../THIRD_PARTY.md) for game-branding and artwork rights.
