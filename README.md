<div align="center">
  <h1>🎮 ForzaBot - Forza Horizon 6 Automation</h1>
  <p>An open-source, computer-vision based automation bot for simple farming races in Forza Horizon 6.</p>
</div>

## 📋 Overview

ForzaBot is a screen-recognition based automation tool designed to farm points/credits in simple "hold gas to finish" races. It uses **OpenCV template matching** to read the game state directly from your screen and simulates keyboard inputs using hardware scan codes (`pydirectinput-rgx`), making it completely undetectable by standard input hooks.

**Note:** Since this bot relies on image recognition, **you must train it yourself** by taking screenshots of your own game. Pre-trained images from other users will likely fail due to different screen resolutions, graphics settings, and UI scaling!

## ✨ Features

- 🖥️ **Real-Time Screen Recognition:** Uses `mss` and OpenCV for fast, lightweight screen capture and template matching.
- ⌨️ **DirectX Input Simulation:** Uses hardware scan codes to bypass DirectX game limitations where standard virtual inputs are ignored.
- 🎨 **Modern GUI:** Easy-to-use dark-themed graphical interface.
- 🎯 **Built-in Training Tool:** Easily capture and assign game states without leaving the app.
- 🔄 **Fully Automated Loop:** Automatically accelerates, skips finish screens, navigates the menu, and restarts the race.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- **Python 3.9 or higher** installed.
- **Administrator Privileges:** You MUST run this script as an Administrator, otherwise the game will ignore the simulated keystrokes.
- **Game Window Mode:** Set your Forza Horizon 6 to **Borderless Windowed** mode for optimal screen capturing.

### 2. Install Dependencies
Clone the repository or download the files, then run:

```bash
pip install -r requirements.txt
```

---

## 📸 Training the Bot (CRITICAL STEP)

The bot doesn't magically know what your game looks like. You need to provide it with 3-5 screenshots for each phase of the race. 

1. Right-click your terminal / command prompt and select **Run as Administrator**.
2. Start the GUI:
   ```bash
   python gui.py
   ```
3. Put the GUI on a second monitor or easily accessible spot. 
4. Click the training buttons in the GUI as you play the game naturally:
   - **🏎️ Racing Screen:** While driving in the race, click the button. Wait 3 seconds, then focus back on the game.
   - **🏁 Race Finished:** When the race concludes and the scoreboard/rewards show up, click this button.
   - **📋 Menu Screen:** When you are at the pre-race menu where you start the event, click this button.
   - **⏳ Loading Screen:** While the game is loading the next race, click this button.
5. **Repeat this at least 3 times for each state** to give the bot a good average of images.

*(Tip: You can use the "✂️ Capture by Region" button to only screenshot specific static UI elements like a "Race Completed" text for higher accuracy.)*

---

## ▶️ Usage

1. Open the game and put your car at the starting line of your farming event.
2. Run `gui.py` **as Administrator**.
3. Ensure all your training data shows a green checkmark ✅.
4. Click **▶ START**.
5. Focus your game window immediately.
6. The bot will now take over.

**Emergency Stop:** Press `F12` on your keyboard at any time to instantly stop the bot, or click the **■ STOP** button in the GUI.

---

## ⚙️ Customizing Keybinds

By default, the bot holds `W` during races, presses `X` at the finish screen, and presses `Enter` in the menu. 
If your layout is different, you can edit the `STATE_ACTIONS` dictionary inside `config.py` using any standard text editor.

---

## ⚠️ Disclaimer & Fair Use

- This tool was created for **educational purposes** to demonstrate computer vision and state machines in Python.
- **Use offline only:** Using automation tools in online/multiplayer lobbies violates the Xbox/Microsoft Terms of Service and can result in a permanent ban. 
- The developer is not responsible for any bans or account suspensions resulting from the use of this software. Please use responsibly in offline solo events.
