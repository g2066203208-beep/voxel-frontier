# Voxel Frontier Roadmap

## Engineering baseline
- TypeScript strict mode
- Vite production bundling
- Three.js renderer isolated from world data
- Input, player physics, HUD, world storage and terrain generation split into modules
- GitHub Actions type-check/build gate before deployment

## Phase 0 — Playable browser slice
- Procedural voxel terrain
- First-person controller
- Block break/place
- Hotbar
- Static web deployment

## Phase 1 — World architecture
- Chunk streaming and dirty-chunk remeshing
- Seeded world generation
- Save/load format
- Better collision and step climbing
- Texture atlas and original art direction
- Worker-based terrain/mesh generation

## Phase 2 — Survival sandbox systems
- Inventory
- Crafting
- Tools and durability
- Health / stamina
- Day-night and weather
- Basic creatures

## Phase 3 — Large-world content
- Biomes
- Structures and cities
- NPCs and factions
- Vehicles
- Machines and power systems

## Phase 4 — Extensibility
- Data-driven block/item/entity registry
- Versioned Mod API
- ZIP mod-pack loader
- Manifest validation
- Sandboxed permissions and compatibility gates

## Phase 5 — Online
- Authoritative multiplayer server
- Player persistence
- Shared worlds
- Mod compatibility handshake
