# Faithbound Mobile RPG Prototype

Native Android vertical slice for the new mobile RPG concept.

## Implemented through v0.3
- NativeActivity + C++20 + OpenGL ES 3 renderer
- Splash/logo, main menu, Android Back navigation
- 3 save slots and autosave
- Faith choice: Established God / Newborn God / Godless
- Character customization: body, skin, hair, outfit
- Seeded finite layered world
- Rotatable 90-degree isometric tile view
- Z layers: surface and underground
- Touch joystick, contextual eat/place/dig controls
- HP / hunger / stamina / day cycle
- Procedural trees, rocks, berries, ores
- Gathering and survival with edible berries, fed healing, safe pickups and atomic crafting
- Resurrection rules tied to faith; Godless is permadeath
- Deterministic O(1) chunk lookup cache, reduced chunk-generation cost and visible-face culling

This is a playable systems prototype, not content-complete production gameplay.
