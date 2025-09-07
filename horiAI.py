is_speaking = False
# new imports for Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import asyncio
import edge_tts
import playsound
import speech_recognition as sr
import webbrowser
import wikipedia
import pygetwindow as gw
import pyautogui
import os
import time
import random
import tkinter as tk
from threading import Thread
from tkinter import  Scrollbar, Text, END, DISABLED, NORMAL
from PIL import Image, ImageTk, ImageSequence
import re
import requests


OPENROUTER_API_KEY = "------ENTER YOUR OPENROUTER API KEY HERE--------"

def get_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "max_tokens": 30,
        "messages": [
            {
                "role": "system",
                "content": "You are a cute anime-style assistant. Always reply in only 5 to 8 words. Be brief, casual, and natural.and don't uses emojis. speak like im your boss "
            },
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("API error:", e)
        return "Sorry, I had a little brain freeze..."


import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


listener = sr.Recognizer()

responses = {
    

}


import edge_tts
import time
import os
import playsound
import re

is_speaking = False

# ✅ Function to remove emojis from text
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        u"\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        u"\U0001F1E0-\U0001F1FF"  # Flags
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols
        u"\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# ✅ Main speak function
async def speak(text):
    global is_speaking
    if is_speaking:
        return
    is_speaking = True

    # Remove emojis before speaking
    clean_text = remove_emojis(text)
    print("AI:", clean_text)

    filename = f"output_{int(time.time() * 800)}.mp3"

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice="en-US-JennyNeural",
        rate="-10%",
        pitch="+30Hz"
    )

    await communicate.save(filename)
    playsound.playsound(filename)

    try:
        os.remove(filename)
    except PermissionError:
        print(f"Could not delete {filename}, it might still be playing.")

    is_speaking = False


def listen_command():
    with sr.Microphone() as source:
        print("Listening...")
        listener.adjust_for_ambient_noise(source)
        audio = listener.listen(source, phrase_time_limit=5)
    try:
        command = listener.recognize_google(audio).lower()
        print("You:", command)
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "network error"

async def open_any_website(command):
    known_sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "instagram": "https://www.instagram.com",
        "chatgpt": "https://chat.openai.com",
        "github": "https://github.com",
        "spotify": "https://open.spotify.com"
    }
    for name, url in known_sites.items():
        if name in command:
            await speak(f"Opening {name}")
            await asyncio.to_thread(webbrowser.open, url)
            return True
    if "open" in command:
        site = command.split("open")[-1].strip().replace(" ", "")
        url = f"https://www.{site}.com"
        await speak(f"Trying to open {site}")
        await asyncio.to_thread(webbrowser.open, url)
        return True
    return False

import pygetwindow as gw

async def close_application(command):
    keyword = command.replace("close", "").replace("app", "").strip().lower()
    found = False

    for window in gw.getWindowsWithTitle(''):
        title = window.title.lower()
        if keyword in title:
            try:
                window.close()
                await speak(f"Closed window with {keyword}")
                found = True
                break
            except:
                continue

    if not found:
        await speak(f"No window found containing '{keyword}'")


async def search_anything(command):
    if "search" in command:
        command = command.lower()

      
        query = command.replace("search", "").replace("for", "").strip()

        if "youtube" in command:
            query = query.replace("on youtube", "").strip()
            await speak(f"Searching YouTube for {query}")
            await asyncio.to_thread(webbrowser.open, f"https://www.youtube.com/results?search_query={query}")

        elif "chat gpt" in command:
            query = query.replace("on chat gpt", "").strip()
            await speak(f"Searching ChatGPT for {query}")
            await asyncio.to_thread(webbrowser.open, f"https://chat.openai.com/?q={query}")

        else:
            query = query.replace("on google", "").strip()
            await speak(f"Searching Google for {query}")
            await asyncio.to_thread(webbrowser.open, f"https://www.google.com/search?q={query}")


async def repeat_after_me(command):
        if "repeat after me" in command:
           to_repeat = command.split("repeat after me ",)[-1].strip()
        elif "say" in command:
           to_repeat = command.split("say",)[-1].strip()
        else:
            return False  

        if to_repeat:
           await speak(to_repeat)
           return True

        return False

async def tell_about_topic(command):
    trigger_phrases = ["do you know about", "tell me about", "what do you know about"]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                await speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                await speak(f"There are multiple entries for {topic}. Please be more specific.")
            except wikipedia.exceptions.PageError:
                await speak(f"I couldn't find any information about {topic}.")
            return True
    return False

async def explain_meaning(command):
    trigger_phrases = ["what do you mean by", "define", "explain",]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                await speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                await speak(f"There are multiple meanings of {topic}. Can you be more specific?")
            except wikipedia.exceptions.PageError:
                await speak(f"I couldn't find the meaning of {topic}.")
            return True
    return False





import re

async def set_timer(command):
   
    pattern = r"timer for (\d+)\s*(seconds|second|minutes|minute)"
    match = re.search(pattern, command.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        seconds = value if "second" in unit else value * 60
        await speak(f"Timer set for {value} {unit}")
        await asyncio.sleep(seconds)
        await speak(f"Time's up! Your {value} {unit} timer has finished.")
    else:
        await speak("Sorry, I couldn't understand the timer duration.")



import datetime

async def time_based_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        await speak("Good morning! How can I help you today?")
    elif 12 <= hour < 17:
        await speak("Good afternoon sir, need help?")
    elif 17 <= hour < 22:
        await speak("Good evening! Need any assistance?")
    else:
        await speak("Hello! It's quite late. Do you need help with something?")



async def tell_about_person(command):
    name = command.replace("tell me about", "").replace("who is", "").strip()
    try:
        summary = wikipedia.summary(name, sentences=2)
        await speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        await speak(f"There are multiple people named {name}. Please be more specific.")
    except wikipedia.exceptions.PageError:
        await speak(f"I couldn't find any information about {name}.")

import pyautogui

# async def play_song_on_spotify(command):
#     if "play" in command and "spotify" in command:
#         song = command.replace("play", "").replace("on spotify", "").strip()
#         await speak(f"Playing {song} on Spotify")
#         await asyncio.to_thread(webbrowser.open, f"https://open.spotify.com/search/{song}")
#         await asyncio.sleep(5)  
#         pyautogui.press('tab', presses=5, interval=0.3)  
#         pyautogui.press('enter')
#         await asyncio.sleep(1)  
#         pyautogui.press('space') 
# NEW AND IMPROVED FUNCTION
# FINAL, MOST RELIABLE VERSION
# FINAL AND CORRECTED VERSION
# FINAL VERSION 2 - MORE DIRECT METHOD
async def play_song_on_spotify(command):
    song = command.replace("play", "").replace("on spotify", "").strip()
    await speak(f"Let's find {song} on Spotify.")

    def spotify_task():
        try:
            from urllib.parse import quote

            driver_service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=driver_service)
            wait = WebDriverWait(driver, 30)

            # --- NEW LOGIC ---
            # 1. Construct a direct search URL
            search_url = f"open.spotify.com/search/{quote(song)}"
            
            # 2. Go directly to the search results
            driver.get(search_url)

            # Wait for and click the "Accept Cookies" button if it appears
            try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
                cookie_button.click()
            except Exception as e:
                print("Cookie button not found or not needed, continuing...")

            # 3. Wait for the play button on the first track and click it
            # This selector is more specific to the main play button of a tracklist.
            play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="tracklist-row"] button[data-testid="play-button"]')))
            play_button.click()
            
            time.sleep(300)
            driver.quit()

        except Exception as e:
            # This is the important part!
            print("--- SPOTIFY AUTOMATION FAILED ---")
            print(f"An error occurred: {e}")
            print("--- END OF ERROR ---")

    Thread(target=spotify_task).start()





async def handle_small_talk(command):
    command = command.lower()
    for key in responses:
        if key in command:
            await speak(random.choice(responses[key]))
            return True
    return False

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VIONEX AI")
        self.root.geometry("800x700")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        


        self.canvas = tk.Canvas(self.root, width=800, height=700, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        gif = Image.open(resource_path("elf2.gif"))
        frame_size = (800, 600)
        self.frames = [ImageTk.PhotoImage(img.resize(frame_size, Image.LANCZOS).convert('RGBA'))
                       for img in ImageSequence.Iterator(gif)]
        self.gif_index = 0
        self.bg_image = self.canvas.create_image(0, 0, anchor='nw', image=self.frames[0])
        self.animate()

        self.root.configure(bg="#000000")
        

        self.chat_log = Text(
            self.root,
            
            bg="#000000",       # Match the transparent color
            fg="sky blue",
            font=("Consolas", 10,),
            wrap='word',
            
            bd=0
        )
        self.chat_log.place(x=0, y=600, width=800, height=100)
        self.chat_log.insert(END, "[System] Type your command below or press F2 to speak.\n")
        self.chat_log.config(state=tk.DISABLED)

        scrollbar = Scrollbar(self.chat_log)
        scrollbar.pack(side="right", fill="y")

        self.entry = tk.Entry(self.root, font=("Segoe UI", 13), bg="#1a1a1a", fg="white", bd=3, insertbackground='white')
        self.entry.place(x=20, y=670, width=700, height=30)
        self.entry.bind("<Return>", self.send_text)

        send_button = tk.Button(self.root, text="Send", command=self.send_text, bg="#222222", fg="white", relief='flat')
        send_button.place(x=730, y=670, width=50, height=30)

        self.root.bind("<F2>", lambda e: Thread(target=self.listen_voice).start())
        # Inside AssistantGUI.__init__(self):
        Thread(target=lambda: asyncio.run(time_based_greeting())).start()


    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)  # Keeps looping


    def send_text(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, END)
        if user_input:
            self.add_text("You: " + user_input)
            Thread(target=lambda: asyncio.run(self.handle_command(user_input))).start()


    def add_text(self, text):
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(END, text + "\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(END)

    def listen_voice(self):
        self.add_text("[System] Listening...")
        command = listen_command()
        if command:
            self.add_text("You: " + command)
            Thread(target=lambda: asyncio.run(self.handle_command(command))).start()

    




    async def handle_command(self, command):
        if command == "network error":
            self.add_text("[System] Network error")
            await speak("Network error.")
            return

        if await handle_small_talk(command):
            return

        if "open" in command:
            if await open_any_website(command):
                return

        if "close" in command:
            await close_application(command)
            return
        
        if "timer" in command:
           await set_timer(command)
           return

        if await repeat_after_me(command):
           return

        if "search" in command:
            await search_anything(command)
            return
        
        if await explain_meaning(command):
           return

        if await tell_about_topic(command):
           return


        if "tell me about" in command or "who is" in command:
            await tell_about_person(command)
            return

        if "play" in command and "spotify" in command:
            await play_song_on_spotify(command)
            return

        if "exit" in command:
            self.add_text("[System] Exiting...")
            await speak("Goodbye!")
            self.root.quit()
            return

        # Fallback to OpenRouter GPT-based smart reply
        self.add_text("[System] Thinking...")
        reply = get_ai_response(command)
        await speak(reply)
        self.add_text("AI: " + reply)
        

def main():
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()