# Paint (H)it

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-0.8.2-orange)

A fun, easy-to-play target shooting game with personalization options. Change the background to your favorite image and add your own custom faces to the targets for a more unique and entertaining experience.

## Features

* **Two Exciting Game Modes:**
    * **Classic Mode:** Test your endurance! You have 5 lives. Lose a life for every target that gets past you. Aim for the highest score!
    * **Timed Challenge:** A true test of speed and accuracy. Score as many points as you can before the timer runs out.
* **Dynamic Combo System:** Hitting the bullseye grants you bonus points and builds your combo multiplier. Keep the streak alive for a massive score!
* **Full Customization:**
    * **Custom Faces:** Upload your own images to appear on the targets! Use the in-game file explorer to select up to four different faces.
    * **Custom Backgrounds:** Don't like the default background? Choose any image from your computer to serve as the game's backdrop.
* **Persistent High Scores:** Your top 10 scores are saved locally, so you can always fight to beat your personal best.
* **Adjustable Difficulty:** Choose from Easy, Normal, or Hard settings to change the speed of the targets.

## Installation

To set up the application, you'll first need to install the required Python packages. It's recommended to use a virtual environment.

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://github.com/eth08/paint_hit.git
    cd paint_hit
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * On Windows: `venv\Scripts\activate`
    * On macOS/Linux: `source venv/bin/activate`

4.  **Install dependencies from `requirements.txt`:**
    
    Install the packages:
    ```bash
    pip install -r requirements.txt
    ```
## Getting Started

1.  **Place Assets:**
    Make sure the following asset files are in the same directory as `paint_hit.py`:
    * `background.jpg` (or your own custom background)
    * `gun.png`
    * `silhouette.png`
    * `target.jpg`
    * `question_mark.png`
    * `splat_red.png`, `splat_green.png`, `splat_blue.png`, `splat_yellow.png`

2.  **Run the game:**
    ```bash
    python paint_hit.py
    ```

## How to Play

* **Aim:** Move your mouse left and right to aim the paint gun.
* **Shoot:** Click the **left mouse button** to shoot.
* **Change Colors:** Use the number keys `1`, `2`, `3`, `4` to switch between Red, Green, Blue, and Yellow paint.
* **Pause:** Press `P` to pause the game.
* **Restart/Quit:** While in-game, press `R` to restart or `Q` to quit to the main menu.

### Scoring

* **Bullseye:** **10 points** + builds combo
* **Target Body:** **5 points**
* **Silhouette:** **1 point**
* **Custom Face:** **5 points**

## Customization

You can customize the game's visuals through the **Settings** menu.

* **To change the background:** Go to `Settings -> Background`. This will open a file explorer where you can navigate to and select any `.jpg` or `.png` file on your computer.
* **To add custom faces:** Go to `Settings -> Faces`. Click any of the four slots to open the file explorer and select an image. These images will then randomly appear on the targets you shoot!

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
