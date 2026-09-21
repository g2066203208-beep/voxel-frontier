# 神契荒境 / Faithbound Mobile RPG

Native Android C++ sandbox RPG prototype.

## v0.3 WorldSim Alpha

### Core technology
- Android NativeActivity
- C++20
- OpenGL ES 3
- 60 Hz fixed-step simulation
- 512 x 512 x 32 finite voxel world
- 16 x 16 procedural chunks with LRU cache
- exposed-face voxel rendering and distance detail reduction
- deterministic seeded generation
- runtime Chinese glyph atlas using Android system fonts
- private binary save files with checksums

### World
- 3D voxel terrain: grass, dirt, stone, sand, water, ore and caves
- biome simulation: plains, forest, coast, highland, dryland
- procedural roads connecting three settlement anchors
- visible settlement houses
- travelling merchant traffic between settlements
- surface resources: trees, rocks, berries and grass
- seasons: spring, summer, autumn and winter
- weather: clear, cloudy, rain, storm and fog
- time-of-day lighting and weather lighting
- player block destruction and placement
- persistent world edits

### Character
- 2D billboard character inside the 3D voxel world
- skin, hair, body and outfit customization
- selectable talent/background
- selectable personality tendency
- attributes: strength, agility, vitality, intelligence, willpower, charisma, luck
- personality: bravery, sociability, discipline, curiosity, empathy
- skills: gathering, mining, combat, crafting, survival, social
- needs: health, hunger, thirst, stamina, sanity, mood and body temperature
- simple walk animation and held-tool visuals

### Survival and RPG
- hunger/thirst/temperature/sanity simulation
- weather and darkness affect survival
- campfires, torches and shrines affect survival state
- rabbits, deer, wolves and slimes
- wildlife flee/chase behavior
- combat and meat drops
- resurrection for believers
- permanent death for godless characters

### Inventory / crafting
- 30-slot inventory
- 8-slot hotbar
- head/body/main-hand/off-hand equipment
- item stacks and tool durability
- dropped item pickup
- consumables and refillable water flask
- multi-tier crafting tree
- hand crafting / workbench / furnace / campfire
- wood, stone and iron progression
- placeable workbench, campfire, furnace and chest voxels

### Society
- NPC roles: merchant, guard, lumberjack, farmer and resident
- NPC personalities and mood
- NPC movement around settlements
- dialogue and relationship values
- charisma / relation / personality / social-skill price modifiers
- buying and selling with coins
- finite merchant coin supply
- settlement discovery and rumor information
- regional reputation

### Faith
- Mature God / Newborn God / Godless starts are structurally different
- mature believers spawn near an existing settlement
- newborn faith starts from a lone shrine
- prayer and offerings
- devotion, followers and shrine levels
- shrine upgrading
- preaching to NPCs using relationship, charisma and personality
- converted NPCs increase followers and divine power
- godless run keeps permanent-death rule

## Branch
Development branch: `mobile-rpg-v3-worldsim`

This is still an alpha systems prototype. Art assets, animation sets, settlement simulation, farming, building interiors, pathfinding, deeper economy and persistence scaling remain active development areas.
