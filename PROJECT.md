# Voxel Frontier — RPG Sandbox Roadmap

## Engineering baseline — DONE
- TypeScript strict mode
- Vite production bundling
- Three.js renderer isolated from world data
- Core / render / systems / UI / world modules
- GitHub Actions type-check/build gate

## Phase 0 — Browser voxel foundation — DONE
- Procedural voxel terrain
- First-person controller
- Collision and gravity
- Raycast targeting
- Block break/place
- Static web build

## Phase 1 — Survival + destruction + building — CURRENT
### Completed in Alpha 0.3
- Health / hunger / stamina
- Stamina-limited sprint
- Starvation, healing, fall damage, death and respawn
- Block hardness and hold-to-break progress
- Physical item drops and proximity pickup
- Typed inventory counts
- Food item and consumption
- Material-consuming building
- Placement validity preview
- Day/night lighting cycle

### Next hardening tasks
- Chunk streaming and dirty-chunk remeshing
- Seeded world generation
- Save/load persistence
- Texture atlas and original art direction
- Step climbing and improved collision
- Worker-based terrain/mesh generation

## Phase 2 — RPG survival systems
- Full inventory window and item stacks
- Crafting and recipes
- Tools, mining efficiency and durability
- Weapons, armor and equipment slots
- Damage types and status effects
- Experience, character level and skill progression
- Weather and temperature exposure

## Phase 3 — Living world
- Neutral and hostile creatures
- Combat AI and pathfinding
- Loot tables
- Biomes
- Resource distribution
- Structures, camps and dungeons

## Phase 4 — RPG content
- NPCs and factions
- Dialogue
- Quests
- Traders and economy
- Villages and cities
- Procedural points of interest
- Boss encounters

## Phase 5 — Large sandbox systems
- Vehicles and mounts
- Machines and power systems
- Farming
- Base defense
- World events

## Phase 6 — Extensibility
- Data-driven block/item/entity registry
- Versioned Mod API
- ZIP mod-pack loader
- Manifest validation
- Sandboxed permissions and compatibility gates

## Phase 7 — Online
- Authoritative multiplayer server
- Player persistence
- Shared worlds
- Server-side combat/state validation
- Mod compatibility handshake
