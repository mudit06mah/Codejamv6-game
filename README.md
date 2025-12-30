# Vanitas

**Vanitas** is a 2D side-scrolling action game built with **Python and Pygame**, focusing on deliberate combat, boss encounters, and narrative sacrifice.

The game explores loss through mechanics: abilities are gained by giving up memories, and each boss fight represents a different combat philosophy.

---

## 🎮 Gameplay Overview

- Single-player, 2D side-view combat
- Two major boss encounters:
  - **Papia** – a ranged, pattern-based spellcaster
  - **Harus** – a melee boss built around timing and counterplay
- Narrative progression through cutscenes and dialogue
- Simple controls with precise combat timing

---

## 🕹 Controls

| Action        | Key |
|--------------|-----|
| Move Left    | A   |
| Move Right   | D   |
| Jump         | W   |
| Attack       | J   |
| Dash (unlockable) | K |
| Confirm / Continue | SPACE |

---

## 🧠 Core Mechanics

- **Memory Sacrifice System**  
  Progression requires sacrificing memories to gain abilities (e.g., Dash).

- **Boss-Focused Combat**  
  Each boss is designed with a unique combat contract:
  - Papia tests positioning and pattern recognition.
  - Harus tests timing, spacing, and counter windows.

- **Screen Shake & Telegraphing**  
  Visual feedback is used to clearly communicate danger and impact.

---

## 🗂 Project Structure

```text
.
├── main.py        # Main game loop and state management
├── player.py      # Player movement, combat, and animations
├── bosses.py      # Boss logic (Papia and Harus)
├── story.py       # Cutscenes and dialogue systems
├── settings.py    # Constants, colors, game states, helpers
├── assets/        # Sprites, sound effects, UI elements
