import time
from pynput.mouse import Listener as MouseListener, Controller as MouseController, Button
from pynput.keyboard import Listener as KeyboardListener, Key
from pynput.keyboard import Controller as KeyboardController
from threading import Thread
import random
import pickle

keyboard = KeyboardController()
recorded_actions = []
start_time = None
stop_script = False
mouse = MouseController()

runtime_minutes = int(input("Enter the number of minutes you want the script to run for: "))
script_start_time = time.time()
script_end_time = script_start_time + runtime_minutes * 60

def save_script(filename):
    with open(filename, 'wb') as f:
        pickle.dump(recorded_actions, f)
    print(f"Script saved as {filename}.")

def load_script(filename):
    global recorded_actions
    with open(filename, 'rb') as f:
        recorded_actions = pickle.load(f)
    print(f"Script loaded from {filename}.")

def on_move(x, y):
    global recorded_actions, start_time
    if start_time is not None:
        recorded_actions.append(('move', time.time() - start_time, (x, y)))

def on_click(x, y, button, pressed):
    global recorded_actions, start_time
    if start_time is not None:
        action = 'click' if pressed else 'release'
        recorded_actions.append((action, time.time() - start_time, (x, y)))

def playback():
    global stop_script, start_time, script_start_time, script_end_time

    while not stop_script:
        if time.time() > script_end_time:  # Check if the script has been running for more than the specified time
            print("Script has been running for the specified time. Stopping playback...")
            stop_script = True
            return
        
        current_runtime_seconds = time.time() - script_start_time
        minutes, seconds = divmod(current_runtime_seconds, 60)
        print(f"Current runtime: {int(minutes)} minutes {int(seconds)} seconds")


        playback_start_time = time.time()
        for action, action_time, pos in recorded_actions:
            while time.time() - playback_start_time < action_time:
                if stop_script:
                    return
            if action == 'move':
                mouse.position = pos
            elif action == 'click':
                mouse.press(Button.left)
                time.sleep(random.randint(50, 150) / 1000)
            elif action == 'release':
                mouse.release(Button.left)
                time.sleep(random.randint(50, 150) / 1000)
            elif action == 'key_press':
                keyboard.press(pos)
                time.sleep(random.randint(50, 150) / 1000)
            elif action == 'key_release':
                keyboard.release(pos)
                time.sleep(random.randint(50, 150) / 1000)

        start_time = None  # Reset start_time after each playback

def on_press(key):
    global recorded_actions, start_time, stop_script, script_start_time, script_end_time
    if key == Key.up:
        print("Recording started...")
        start_time = time.time()
        recorded_actions = []
    elif key == Key.down:
        print("Recording stopped...")
        start_time = None
        filename = input("Enter a name for the script: ")
        save_script(filename)  # Save the script when recording stops
    elif key == Key.right:
        print("Playback started...")
        stop_script = False
        script_start_time = time.time()
        script_end_time = script_start_time + runtime_minutes * 60  # Reset the script end time
        Thread(target=playback).start()
    elif key == Key.left:
        print("Script stopped...")
        stop_script = True

    elif start_time is not None:
        recorded_actions.append(('key_press', time.time() - start_time, key))


    elif start_time is not None:
        recorded_actions.append(('key_press', time.time() - start_time, key))

def on_release(key):
    global recorded_actions, start_time
    if start_time is not None:
        recorded_actions.append(('key_release', time.time() - start_time, key))

if __name__ == "__main__":
    choice = input("Do you want to load a saved script? (yes/no): ")
    if choice.lower() == 'yes':
        filename = input("Enter the name of the script: ")
        load_script(filename)

with MouseListener(on_move=on_move, on_click=on_click) as mouse_listener, KeyboardListener(on_press=on_press, on_release=on_release) as keyboard_listener:
    mouse_listener.join()
    keyboard_listener.join()
