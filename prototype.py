from pynput.mouse import Listener as MouseListener, Controller as MouseController, Button
from pynput.keyboard import Listener as KeyboardListener, Key
from pynput.keyboard import Controller as KeyboardController
from threading import Thread
from PIL import ImageGrab, Image
import time
import random
import pickle
import pytesseract
import pyautogui
import cv2
import numpy as np
import re

keyboard_controller = KeyboardController()
recorded_actions = []
start_time = None
stop_script = False
mouse_controller = MouseController()
is_playing = False

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
        recorded_actions.append((action, time.time() - start_time, button))

def read_numbers_from_screen():
    screen_width, screen_height = pyautogui.size()

    left = 350
    top = screen_height // 2 + 542
    right = screen_width // 2 - 330
    bottom = screen_height - 135

    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
    
    screenshot_np = np.array(screenshot)

    grayscale = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

    inverted_grayscale = 255 - grayscale

    thresholded = cv2.adaptiveThreshold(inverted_grayscale, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 3)

    thresholded_image = Image.fromarray(thresholded)

    text = pytesseract.image_to_string(thresholded_image, config='--psm 7')

    numbers_with_commas_or_periods = re.findall(r'\d+(?:[.,]\d+)*', text)
    
    numbers = [int(number.replace(',', '').replace('.', '')) for number in numbers_with_commas_or_periods if int(number.replace(',', '').replace('.', '')) >= 10000]

    return numbers[0] if numbers else None

def playback():
    global stop_script, start_time, script_start_time, script_end_time, is_playing

    number_list = []
    total_profit = 0
    is_playing = True

    while not stop_script:
        if time.time() > script_end_time:
            print("Script has been running for the specified time. Stopping playback...")
            stop_script = True
            return
        
        current_runtime_seconds = time.time() - script_start_time
        minutes, seconds = divmod(current_runtime_seconds, 60)
        print(f"Current runtime: {int(minutes)} minutes {int(seconds)} seconds")

        playback_start_time = time.time()
        for action, action_time, button in recorded_actions:
            while time.time() - playback_start_time < action_time:
                if stop_script:
                    return
            if action == 'move':
                mouse_controller.position = button

            elif action == 'click':
                if button == Button.middle:
                    number = read_numbers_from_screen()

                    if number is not None and (not number_list or number not in number_list):
                        number_list.append(number)

                    if number_list and len(str(number_list[0])) == 6:
                        number_list.pop(0)
                    if len(number_list) == 2 and number_list and len(str(number_list[1])) == 6:
                        number_list.pop(1)
                    print(number_list)
                    if len(number_list) >= 3:
                        total_profit += -number_list[0] - number_list[1] + number_list[2]
                        number_list = []
                else:
                    mouse_controller.press(Button.left)
                    time.sleep(random.randint(50, 150) / 1000)
                
            elif action == 'release':
                if button == Button.left:
                    mouse_controller.release(Button.left)
                    time.sleep(random.randint(50, 150) / 1000)

            elif action == 'key_press':
                keyboard_controller.press(button)
                time.sleep(random.randint(50, 150) / 1000)
            
            elif action == 'key_release':
                keyboard_controller.release(button)
                time.sleep(random.randint(50, 150) / 1000)

        total_time_elapsed = (time.time() - script_start_time) / 3600

        average_profit_per_hour = round(total_profit / total_time_elapsed) if total_time_elapsed > 0 else 0

        print(f"Total profit after this playback loop: {total_profit}")
        print(f"Approximate average profit per hour: {average_profit_per_hour}")

        start_time = None
        is_playing = False

def on_press(key):
    global recorded_actions, start_time, stop_script, script_start_time, script_end_time, is_playing
    if is_playing:
        return
    if key == Key.up:
        print("Recording started...")
        start_time = time.time()
        recorded_actions = []
    elif key == Key.down:
        print("Recording stopped...")
        start_time = None
        filename = input("Enter a name for the script: ")
        save_script(filename)
    elif key == Key.right:
        print("Playback started...")
        stop_script = False
        script_start_time = time.time()
        script_end_time = script_start_time + runtime_minutes * 60
        Thread(target=playback).start()
    elif key == Key.left:
        print("Script stopped...")
        stop_script = True

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