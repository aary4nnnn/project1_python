# Voice-Controlled AI Assistant using Python

This project presents the design and implementation of a voice-controlled AI assistant developed using Python. The assistant enables natural, hands-free interaction with a computer system by recognizing voice commands, understanding user intent, and executing tasks in real time using intelligent automation and conversational AI techniques.

## Abstract
The Voice-Controlled AI Assistant enhances human–computer interaction by integrating speech recognition, natural language processing, text-to-speech synthesis, and task automation. The system captures voice input, converts it to text, interprets user intent using transformer-based AI models, and performs actions such as web navigation, information retrieval, media control, and system automation. Responses are delivered through natural-sounding speech and a graphical user interface, providing an intuitive and efficient user experience.

## Features
- Real-time speech recognition and command processing  
- Transformer-based natural language understanding for context-aware responses  
- Text-to-speech output using modern TTS engines  
- Web automation using Selenium and webdriver-manager  
- Desktop automation using pyautogui  
- Graphical user interface built with tkinter and Pillow (PIL)  
- Asynchronous task handling using asyncio  

## Technologies Used
- Python 3.x  
- SpeechRecognition  
- edge_tts  
- OpenRouter API (Transformer-based NLP models)  
- Selenium, webdriver-manager  
- pyautogui  
- tkinter, Pillow (PIL)  
- asyncio  

## System Overview
The assistant follows a hybrid architecture combining lightweight real-time audio preprocessing with transformer-based natural language understanding. Voice input is captured through a microphone, preprocessed for noise reduction, converted to text, and analyzed to infer user intent. Based on the inferred intent, the system executes automated tasks and provides feedback through speech and a graphical interface.

## Modules
- Audio Input and Preprocessing  
- Speech Recognition  
- Natural Language Processing and Intent Analysis  
- Task Automation  
- Text-to-Speech and Response Generation  
- Graphical User Interface  
- Asynchronous Control and Optimization  

## How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/aary4nnnn/project1_python.git

2. Navigate to the project directory:
   ```bash
   cd project1_python
   
3. Install required dependencies:
   ```bash
   pip install SpeechRecognition pyttsx3 selenium pyautogui pillow
   
4. Ensure a working microphone is connected and configured.
   
6. Run the voice assistant:
   ```bash
   python waifuAI.py
