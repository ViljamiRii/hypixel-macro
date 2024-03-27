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

class ScriptRecorder:
    def __init__(self):
        self.keyboard_controller = KeyboardController()
        self.recorded_actions = []
        self.start_time = None
        self.stop_script = False
        self.mouse_controller = MouseController()
        self.is_playing = False
        self.runtime_minutes = int(input("Enter the number of minutes you want the script to run for: "))
        self.script_start_time = time.time()
        self.script_end_time = self.script_start_time + self.runtime_minutes * 60

    def save_script(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.recorded_actions, f)
        print(f"Script saved as {filename}.")

    def load_script(self, filename):
        with open(filename, 'rb') as f:
            self.recorded_actions = pickle.load(f)
        print(f"Script loaded from {filename}.")

    def on_move(self, x, y):
        if self.start_time is not None:
            self.recorded_actions.append(('move', time.time() - self.start_time, (x, y)))

    def on_click(self, x, y, button, pressed):
        if self.start_time is not None:
            action = 'click' if pressed else 'release'
            self.recorded_actions.append((action, time.time() - self.start_time, button))

    @staticmethod
    def round_to_nearest(number, base):
        return base * round(number/base)
    
    @staticmethod
    def post_process(text):
        return text.replace('8', '0').replace('6', '0')

    def read_numbers_from_screen(self):
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
        text = self.post_process(text)

        numbers_with_commas_or_periods = re.findall(r'\d+(?:[.,]\d+)*', text)
        
        numbers = [int(number.replace(',', '').replace('.', '')) for number in numbers_with_commas_or_periods if int(number.replace(',', '').replace('.', '')) >= 10000]

        return numbers[0] if numbers else None

    
    def playback(self):
        self.number_list = []
        self.total_profit = 0
        self.is_playing = True

        while not self.stop_script:
            if time.time() > self.script_end_time:
                print("Script has been running for the specified time. Stopping playback...")
                self.stop_script = True
                return
            
            current_runtime_seconds = time.time() - self.script_start_time
            minutes, seconds = divmod(current_runtime_seconds, 60)
            print(f"Current runtime: {int(minutes)} minutes {int(seconds)} seconds")

            playback_start_time = time.time()
            for action, action_time, button in self.recorded_actions:
                while time.time() - playback_start_time < action_time:
                    if self.stop_script:
                        return
                if action == 'move':
                    self.mouse_controller.position = button

                elif action == 'click':
                    if button == Button.middle:
                        number = self.read_numbers_from_screen()

                        if number is not None and (not self.number_list or number not in self.number_list):
                            if len(self.number_list) < 2:
                                number = self.round_to_nearest(number, 10000)
                            else:
                                number = self.round_to_nearest(number, 100000)
                            self.number_list.append(number)
                            
                        if len(self.number_list) >= 3:
                            self.total_profit += -self.number_list[0] - self.number_list[1] + self.number_list[2]
                            self.number_list = []
                    else:
                        self.mouse_controller.press(Button.left)
                        time.sleep(random.randint(50, 150) / 1000)
                    
                elif action == 'release':
                    if button == Button.left:
                        self.mouse_controller.release(Button.left)
                        time.sleep(random.randint(50, 150) / 1000)

                elif action == 'key_press':
                    self.keyboard_controller.press(button)
                    time.sleep(random.randint(50, 150) / 1000)
                
                elif action == 'key_release':
                    self.keyboard_controller.release(button)
                    time.sleep(random.randint(50, 150) / 1000)

            total_time_elapsed = (time.time() - self.script_start_time) / 3600

            average_profit_per_hour = round(self.total_profit / total_time_elapsed) if total_time_elapsed > 0 else 0

            print(f"Total profit after this playback loop: {self.total_profit}")
            print(f"Approximate average profit per hour: {average_profit_per_hour}")

    def on_press(self, key):
        if self.is_playing:
            return
        if key == Key.up:
            print("Recording started...")
            self.start_time = time.time()
            self.recorded_actions = []
        elif key == Key.down:
            print("Recording stopped...")
            self.start_time = None
            filename = input("Enter a name for the script: ")
            self.save_script(filename)
        elif key == Key.right:
            print("Playback started...")
            self.stop_script = False
            self.script_start_time = time.time()
            self.script_end_time = self.script_start_time + self.runtime_minutes * 60
            Thread(target=self.playback).start()
        elif key == Key.left:
            print("Script stopped...")
            self.stop_script = True

        elif self.start_time is not None:
            self.recorded_actions.append(('key_press', time.time() - self.start_time, key))

    def on_release(self, key):
        if self.start_time is not None:
            self.recorded_actions.append(('key_release', time.time() - self.start_time, key))

if __name__ == "__main__":
    recorder = ScriptRecorder()
    choice = input("Do you want to load a saved script? (yes/no): ")
    if choice.lower() == 'yes':
        filename = input("Enter the name of the script: ")
        recorder.load_script(filename)

    with MouseListener(on_move=recorder.on_move, on_click=recorder.on_click) as mouse_listener, KeyboardListener(on_press=recorder.on_press, on_release=recorder.on_release) as keyboard_listener:
        mouse_listener.join()
        keyboard_listener.join()