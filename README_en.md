# 🦀 Auto_Spotify: The AI that manages your in-game music

[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](README.md)

Auto_Spotify is a smart Python script that listens to your video game audio. As soon as it hears action (gunshots, in-game music, cutscenes), it automatically mutes Chrome/Spotify. When the silence returns, your music resumes on its own!

---

## 🛠️ Part 1: Installation and Prerequisites

For the AI to run on your machine, you need a functional Python environment and a few libraries.

1. Install **Python 3.9 or higher** on your computer.
2. Open your terminal (or command prompt) in the project folder.
3. Update your package manager to avoid installation errors:
   * **On Windows:** `python -m pip install --upgrade pip`
   * **On Linux:** `sudo apt update && sudo apt install python3-pip`
4. Install all the necessary dependencies by running this command:
   `pip install tensorflow tensorflow-hub numpy sounddevice keyboard pycaw comtypes`
5. **On the very first launch of the script**, the artificial intelligence (Google's YAMNet model) will automatically download into a `cerveau_ia` folder. This takes a few seconds and requires an internet connection. All subsequent launches will be instantaneous!

---

## 🎧 Part 2: Virtual Cable (Audio Configuration)

**⚠️ Crucial step!** If you skip this, the AI will listen to Spotify, think it's the game, mute Spotify, hear silence, unmute Spotify... and create an infinite loop. You must isolate the game audio using a virtual cable.

### 🪟 For Windows Users

**1. Download VB-Audio Virtual Cable**
1. Go to the official website: [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Download the free Windows version and install it (restarting your PC is highly recommended).

**2. Route the game audio**
1. Open Windows Sound settings > **Volume mixer**.
2. Find your video game in the list of open apps.
3. Change its audio Output to **CABLE Input (VB-Audio Virtual Cable)**.

**3. Hear your game (Routing the Cable to your Headset)**
Since your game is now sending audio to a virtual cable, you won't hear anything in your headset. To fix this, you need to tell Windows to redirect the cable's sound to your ears:
1. Press the **Windows + R** keys on your keyboard to open the "Run" dialog.
2. Type exactly `mmsys.cpl` and press **Enter**. *(This instantly opens the classic Windows Sound control panel)*.
3. At the top of this window, click on the second tab: **Recording**.
4. Look for the **CABLE Output (VB-Audio Virtual Cable)** line, right-click it, and select **Properties**.
5. Open the **Listen** tab.
6. Check the **"Listen to this device"** box.
7. In the dropdown menu right below ("Playback through this device"), **select your main headset or earphones**.
8. Click **Apply**, then **OK**.

### 🐧 For Linux Users (PulseAudio / PipeWire)
On Linux, no third-party software is needed!
1. Open a terminal and create a virtual cable with this command:
   `pactl load-module module-null-sink sink_name=VirtualCable sink_properties=device.description="Virtual_Cable"`
2. Install and open the volume controller: `sudo apt install pavucontrol && pavucontrol`
3. In the **Playback** tab, find your game and redirect its output to **Virtual_Cable**.
4. The AI will need to listen to the "Monitor of Virtual_Cable".

### 🚀 Launch the script
1. Run the `auto_spotify.py` file.
2. The script will scan your devices and ask you to enter a number.
3. Look in the list for the line named exactly **CABLE Output (VB-Audio Virtual Cable)** *(There are several, you must choose the one with the highest number. In my case, it's 24)*. 
4. This choice will be saved for next time. If you encounter a bug during future launches, it's likely from here: simply delete the `config_audio.txt` file to reset it. Have fun playing!

---

## 🧠 Part 3: Features (How does it work?)

This program doesn't just blindly press "Play/Pause". It includes several advanced mechanics to make your gaming experience as smooth and enjoyable as possible. Here's what happens under the hood:

### 🕵️ 1. Smart Listening & "Eco" Mode (Anti-Overload)
* **Real-time analysis:** The AI (based on the YAMNet model) listens to audio clips of about one second (0.975s) in a loop. It categorizes the sounds it hears and checks if "Music" is its top prediction.
* **Anti-Void Shield:** If your game is completely silent (no sound is sent to the virtual cable), the script detects it instantly. Instead of forcing the neural network to analyze absolute void (which wastes CPU), it bypasses the AI until the next sound!

### 🎚️ 2. Volume Control (Fade In & Fade Out)
This is the flagship feature for your ears' comfort. The script doesn't cut the music abruptly, it acts like a real DJ:
* **Surgical targeting:** The program taps into the Windows volume mixer to specifically find `chrome.exe` (where your Web Spotify or YouTube runs). It memorizes its initial volume.
* **↘️ Fade Out (1.5 seconds):** When the AI hears music in your game, the script gradually lowers Chrome's volume to 0 over 1.5 seconds. The transition is smooth. Once silence is achieved, it simulates pressing the "Pause" media key on your keyboard.
* **↗️ Fade In (5.0 seconds):** When the action settles down, the script presses "Play", then very slowly raises Chrome's volume back up over 5 seconds. Returning to your personal music happens without any auditory shock.

### ⏳ 3. The "Patience" Gauge (7.5 seconds)
To prevent Spotify from randomly turning on and off at the slightest NPC dialogue or brief musical pause in your game, the script uses a patience gauge.
* After muting Spotify, it will wait for an **uninterrupted in-game musical silence of 7.5 seconds** before deciding it's time to resume your music.

### 💾 4. Hardware Memory
* On the first launch, you select your audio device number (Virtual Cable). The program creates a local `config_audio.txt` file to save this choice.
* On subsequent launches, it starts 100% autonomously. *Bonus: if your virtual cable changes numbers due to a Windows update, the script will notice, block the error, and automatically re-open the selection menu for you.*

### 🛑 5. Clean Emergency Stop (Safe Exit)
* Done playing? Simply press `Ctrl + C` in the terminal.
* The script catches this stop command, halts listening, and most importantly: **instantly restores Chrome's volume to its normal state**. You'll never end up with a permanently muted browser because of the program!

---

## ⚙️ Part 4: Customization (For Power Users)

If you find the AI too sensitive or the transitions too slow, you can open `auto_spotify.py` in your code editor and tweak the configuration variables at the very top of the file:

*   `PATIENCE_TIME = 7.5`: The time (in seconds) the script waits before resuming Spotify after a game sound ends.
*   `FADE_OUT_TIME = 1.5`: The speed (in seconds) at which Chrome's volume decreases.
*   `FADE_IN_TIME = 5.0`: The speed (in seconds) at which Chrome's volume increases.

---

## 🆘 Part 5: Support and Troubleshooting

If you encounter an issue using Auto_Spotify, here are the solutions to the most common problems.

*   **The script shows `ModuleNotFoundError` on launch:** 
    You forgot to install the dependencies. Re-run the `pip install ...` command provided in Part 1 in your terminal.
*   **Chrome's volume goes down but the music doesn't stop:** 
    Make sure you are using the official Google Chrome browser and that you haven't disabled or remapped the "Play/Pause" media key on your keyboard.
*   **The AI gets confused and loops (or only hears "White Noise"):** 
    It's listening to the wrong cable. Delete the small `config_audio.txt` file that was created in your folder, then restart the script to reselect the correct device (the highest WASAPI number corresponding to `CABLE Output`).

---

## 📝 License & Credits

*   **Developer:** [Giovanni Kuntz](https://github.com/KrouteDeKiche)
*   **AI Brain:** Powered by the Google YAMNet audio model (via TensorFlow Hub).
*   **License:** Do whatever you want with this code!