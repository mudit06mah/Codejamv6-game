# Vanitas
<img width="1919" height="1077" alt="image" src="https://github.com/user-attachments/assets/8bb9d40f-bacf-45f1-aff3-ab60594c2e44" />


**Vanitas** is a 2D action game built with **Python(Pygame)**, centered around revenge, loss, and the cost of obsession.

The game tells a simple but heavy story:  
in the pursuit of vengeance, you slowly erase the very person you loved.

---

## Story & Themes

We were happily married.  
Then they took her away from me.

I chase the killer, driven by rage and grief. But I am not strong enough.  
To move forward, I must let go.

Progress in *Vanitas* is tied directly to **forgetting**:
- To gain speed, I forget our **first date**
- To survive longer, I forget **her voice**
- To reach the final confrontation, I must forget **her name**

Each sacrifice grants power, but removes meaning.

By the time I finally confront the killer and strike the final blow,  
I succeed.

But I cannot remember who I did it for.

---

## Gameplay Overview

- Single-player 2D side-view action game
- Heavy focus on **boss encounters**
- Narrative progression through cutscenes and dialogue
- Abilities are unlocked by sacrificing memories
- Minimalist design with strong visual telegraphing

---

## Controls

| Action | Key |
|------|----|
| Move Left | A |
| Move Right | D |
| Jump | W |
| Attack | J |
| Dash (unlockable) | K |
| Confirm / Continue | SPACE |

---

## Gameplay Preview

https://drive.google.com/file/d/1HASuVZ-mL2vsHd027esL-EG_skmPEPNN/view

---

## 🗂 Project Structure

```text
.
├── main.py        # Main game loop and state management
├── player.py      # Player movement, combat, and animations
├── bosses.py      # Boss logic and attack patterns
├── story.py       # Cutscenes and dialogue systems
├── settings.py    # Constants, colors, game states, helpers
├── assets/        # Sprites, sound effects, UI elements
├── prototypes/    # Older prototypes for boss mechanics
```

---

## ▶️ How to Run

Requirements

- Python 3.9+
- Pygame

Install dependencies

```bash
pip install pygame
```

Run the game

```bash
python main.py
```

---

##  Assets & Audio
All sprites were drawn by hand
All visual and audio assets are stored in the assets/ directory
