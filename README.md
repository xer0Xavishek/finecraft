# Finecraft

Finecraft is a Minecraft-inspired voxel game prototype built in Python using PyOpenGL and GLUT.
It provides a procedurally generated block world with first-person and third-person camera modes, block interaction, movement physics, and lightweight combat mechanics.

## Project Status

This repository is an educational and experimental game project focused on core voxel gameplay concepts in Python and OpenGL.

## Key Features

- Procedural terrain generation with multiple block types
- First-person and third-person camera views
- Real-time movement and gravity-based physics
- Block breaking and block placement system
- Survival and Creative gameplay modes
- Enemy spawning and projectile combat
- Optional autoshoot mode
- Day/Night and Rain environment toggles
- In-game HUD with controls and player status

## Technology Stack

- Python 3
- PyOpenGL (OpenGL + GLUT)
- Immediate mode rendering with visibility precomputation for world faces

## Repository Structure

```text
/home/runner/work/finecraft/finecraft
├── finecraft.py        # Main game source file and entry point
├── README.md           # Project documentation
├── LICENSE             # License file
└── OpenGL/             # Bundled OpenGL/PyOpenGL-related package files (do not modify)
```

## Requirements

- Python 3.8 or newer (recommended)
- OpenGL-compatible graphics environment
- GLUT runtime support available on your system

## Setup

1. Open a terminal in the project root:
   - `/home/runner/work/finecraft/finecraft`
2. (Optional) Create and activate a virtual environment.
3. Install PyOpenGL dependencies if they are not already available in your environment:

   ```bash
   pip install PyOpenGL PyOpenGL_accelerate
   ```

## Run the Game

From the project root, run:

```bash
python finecraft.py
```

## Controls

### Movement and View

- `W / A / S / D` — Move
- `Mouse Move` — Look around
- `V` — Toggle camera (`FirstPerson` / `ThirdPerson`)

### Vertical Movement

- `Space` — Jump (or move up in God Mode)
- `X` — Move down (God Mode)

### World Interaction

- `Left Mouse Button` — Break targeted block
- `Right Mouse Button` — Place selected block
- `1` to `5` — Select held block type

### Combat and Modes

- `F` — Fire projectile
- `M` — Toggle game mode (`Survival` / `Creative`)
- `G` — Toggle God Mode (noclip/fly/infinite health behavior)
- `C` — Toggle autoshoot

### Environment and UI

- `N` — Toggle Day/Night
- `R` — Toggle Rain
- `H` — Show/Hide help overlay
- `Esc` — Exit game

## Gameplay Notes

- In `Survival` mode, enemies spawn periodically and damage the player on contact.
- In `Creative` mode, enemy entities are cleared and no new enemies are spawned.
- Score increases by breaking blocks and defeating enemies.
- Falling below the world boundary triggers a player reset.

## Troubleshooting

### Window fails to open or crashes at startup

- Confirm your Python environment supports OpenGL and GLUT.
- Ensure graphics drivers are installed and up to date.
- If running remotely or headless, verify that display forwarding/OpenGL context creation is supported.

### Import errors for OpenGL modules

- Install required packages:

  ```bash
  pip install PyOpenGL PyOpenGL_accelerate
  ```

- Ensure the command is executed in the same Python environment used to run the game.

## Contributing

Contributions are welcome. For substantial changes, open an issue first to discuss scope and approach.

## License

This project is distributed under the terms of the license included in `LICENSE`.
