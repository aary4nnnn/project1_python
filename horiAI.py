import os
import sys
import asyncio
import re
import time
import random
import datetime
import pyaudio
import io
from threading import Thread
import tkinter as tk
from tkinter import Scrollbar, Text, END, DISABLED, NORMAL, filedialog
from PIL import Image, ImageTk, ImageSequence

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import webbrowser

import edge_tts
import playsound
import speech_recognition as sr
import requests

import wikipedia
import pygetwindow as gw
import pyautogui

import fitz 
import docx
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

is_speaking = False
OPENROUTER_API_KEY = "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" 

conversation_history = [
    {
        "role": "system",
        "content": "You are a cute anime-style assistant. Always reply in only 5 to 8 words. Be brief, casual, and natural. and don't uses emojis. speak like im your boss "
    }
]

listener = sr.Recognizer()
listener.dynamic_energy_threshold = True
listener.pause_threshold = 1.2

document_text_chunks = []
vector_index = None
print("[System] Loading embedding model. This may take a moment...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("[System] Embedding model loaded.")

responses = {}

def get_ai_response(prompt):
    """
    The "brain" of the AI. It's contextual and can search loaded documents (RAG).
    """
    global conversation_history, vector_index, embedding_model, document_text_chunks

    context_str = ""
    
    if vector_index is not None:
        print("[System] Searching document for context...")
             
        query_embedding = embedding_model.encode([prompt])
               
        D, I = vector_index.search(query_embedding, k=3) 
        retrieved_chunks = [document_text_chunks[i] for i in I[0]]
        context_str = "\n\n--- RELEVANT DOCUMENT CONTEXT ---\n" + "\n\n".join(retrieved_chunks) + "\n---------------------------------\n"
 
    conversation_history.append({"role": "user", "content": prompt + context_str})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": conversation_history
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = response.json()["choices"][0]["message"]["content"]
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"API error: {e}")
        conversation_history.pop() 
        return "Sorry, I had a little brain freeze..."

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F" 
        u"\U0001F300-\U0001F5FF"  
        u"\U0001F680-\U0001F6FF"  
        u"\U0001F1E0-\U0001F1FF"  
        u"\U00002700-\U000027BF" 
        u"\U0001F900-\U0001F9FF"  
        u"\U00002600-\U000026FF"  
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

async def speak(text):
    """
    Speaks the given text using a formal voice and cleans AI tokens.
    """
    global is_speaking
    if is_speaking:
        return
    is_speaking = True
   
    clean_text = remove_emojis(text)
    clean_text = clean_text.replace("<s>", "").replace("</s>", "")
    clean_text = clean_text.replace("[s]", "").replace("[OUT]", "")
    clean_text = clean_text.strip()
    
    if not clean_text:
        is_speaking = False
        return

    print(f"AI: {clean_text}")
    filename = f"output_{int(time.time() * 800)}.mp3"

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice="en-US-AriaNeural", 
        rate="+0%",             
        pitch="+0Hz"               
    )

    await communicate.save(filename)
    playsound.playsound(filename)

    try:
        os.remove(filename)
    except PermissionError:
        print(f"Could not delete {filename}, it might still be playing.")
    is_speaking = False

def listen_command():
    """
    The improved listener: adaptive noise handling and timeouts.
    """
    with sr.Microphone() as source:
        print("Listening...")
        listener.adjust_for_ambient_noise(source, duration=1.5) 
        
        try:
            audio = listener.listen(source, timeout=7, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Listening timed out, no speech detected.")
            return ""
            
    try:
        command = listener.recognize_google(audio).lower()
        print(f"You: {command}")
        return command
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError:
        print("Could not request results; check your network connection")
        return "network error"


def split_text_into_chunks(text, chunk_size=1000, overlap=200):
    """Splits text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def process_document(file_path):
    """
    Extracts text from PDF/DOCX, creates embeddings, and builds the FAISS index.
    """
    global document_text_chunks, vector_index, embedding_model
    
    text = ""
    try:
        if file_path.endswith('.pdf'):
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            print("[System] Extracted text from PDF.")
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            print("[System] Extracted text from DOCX.")
        else:
            print("[System] Unsupported file type.")
            return False
            
        if not text:
            print("[System] No text extracted from document.")
            return False

        
        document_text_chunks = split_text_into_chunks(text)
            
        
        print("[System] Creating embeddings for the document...")
        embeddings = embedding_model.encode(document_text_chunks)
        
       
        d = embeddings.shape[1]
        vector_index = faiss.IndexFlatL2(d)
        vector_index.add(embeddings) 
        
        print(f"[System] Successfully loaded and indexed {len(document_text_chunks)} chunks.")
        return True
        
    except Exception as e:
        print(f"Error processing document: {e}")
        return False
        


async def open_any_website(command):
    """
    Opens websites in the system's DEFAULT browser.
    """
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
    """
    Searches Google or YouTube in the system's DEFAULT browser.
    """
    if "search" in command:
        command = command.lower()
        query = command.replace("search", "").replace("for", "").strip()

        if "youtube" in command:
            query = query.replace("on youtube", "").strip()
            url = f"https://www.youtube.com/results?search_query={query}"
            await speak(f"Searching YouTube for {query}")
            await asyncio.to_thread(webbrowser.open, url) 

        elif "chat gpt" in command:
            query = query.replace("on chat gpt", "").strip()
            url = f"https://chat.openai.com/?q={query}"
            await speak(f"Searching ChatGPT for {query}")
            await asyncio.to_thread(webbrowser.open, url) 

        else:
            query = query.replace("on google", "").strip()
            url = f"https://www.google.com/search?q={query}"
            await speak(f"Searching Google for {query}")
            await asyncio.to_thread(webbrowser.open, url) 

async def repeat_after_me(command):
    if "repeat after me" in command:
        to_repeat = command.split("repeat after me ", 1)[-1].strip()
    elif "say" in command:
        to_repeat = command.split("say", 1)[-1].strip()
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

async def play_song_on_spotify(command):
    """
    Automates Spotify in Chrome.
    """
    song = command.replace("play", "").replace("on spotify", "").strip()
    await speak(f"Let's find {song} on Spotify.")

    def spotify_task():
        try:
            from urllib.parse import quote

            driver_service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=driver_service)
            wait = WebDriverWait(driver, 30)

            search_url = f"https://open.spotify.com/search/{quote(song)}"
            driver.get(search_url)

            try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
                cookie_button.click()
            except Exception as e:
                print("Cookie button not found or not needed, continuing...")

            play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="tracklist-row"] button[data-testid="play-button"]')))
            play_button.click()
            
            time.sleep(300)
            driver.quit()
        except Exception as e:
            print(f"--- SPOTIFY AUTOMATION FAILED: {e} ---")

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

        try:
            gif = Image.open(resource_path("elf2.gif"))
            frame_size = (800, 600)
            self.frames = [ImageTk.PhotoImage(img.resize(frame_size, Image.LANCZOS).convert('RGBA'))
                               for img in ImageSequence.Iterator(gif)]
            self.gif_index = 0
            self.bg_image = self.canvas.create_image(0, 0, anchor='nw', image=self.frames[0])
            self.animate()
        except Exception as e:
            print(f"Error loading GIF: {e}. Make sure 'elf2.gif' is in the same folder.")
            self.bg_image = self.canvas.create_rectangle(0, 0, 800, 600, fill="black")


        self.root.configure(bg="#000000")
        
        self.chat_log = Text(
            self.root,
            bg="#000000",
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

       
        load_button = tk.Button(self.root, text="Load File", command=self.load_file, bg="#222222", fg="white", relief='flat')
        load_button.place(x=20, y=630, width=80, height=30)

        self.root.bind("<F2>", lambda e: Thread(target=self.listen_voice).start())
        Thread(target=lambda: asyncio.run(time_based_greeting())).start()

   
    def load_file(self):
        """Called when the 'Load File' button is clicked."""
        file_path = filedialog.askopenfilename(
            title="Select a PDF or DOCX file",
            filetypes=(("PDF files", "*.pdf"), ("Word files", "*.docx"))
        )
        if not file_path:
            return
            
        self.add_text(f"[System] Loading file: {os.path.basename(file_path)}...")
        Thread(target=self.process_file_thread, args=(file_path,)).start()

    def process_file_thread(self, file_path):
        success = process_document(file_path)
        if success:
            self.add_text(f"[System] File loaded! You can now ask questions about it.")
        else:
            self.add_text("[System] Error: Failed to load the file.")

    def animate(self):
        try:
            self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
            self.gif_index = (self.gif_index + 1) % len(self.frames)
            self.root.after(100, self.animate)
        except Exception:
            pass 

    def send_text(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, END)
        if user_input:
            self.add_text(f"You: {user_input}")
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
            self.add_text(f"You: {command}")
            Thread(target=lambda: asyncio.run(self.handle_command(command))).start()
        else:
            self.add_text("[System] Listening timed out or failed.")

    async def handle_command(self, command):
        """
        Main command router. Tries skills first, then falls back to AI.
        """
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

        self.add_text("[System] Thinking...")
        reply = get_ai_response(command) 
        
        await speak(reply) 
        self.add_text(f"AI: {reply}")
        
def main():
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()