# Alicia the AI
i have vibe coded this projec still i understood the archeticture andd coding of this project .
this is the hand made archetiture for alicia made by me 
![Alicia](resources/image.png)

## 🧠 About Alicia

**Alicia** is a personal AI voice assistant designed to interact with the user through natural speech.

The project is being built as a modular system where different components handle different responsibilities — from detecting speech and converting it to text, to processing commands, interacting with external tools, storing information, and responding through voice.

The goal is to build Alicia from the ground up rather than relying on a single monolithic script.

---

## ✨ Features

- 🎙️ Voice input and speech processing
- 🧠 AI-powered command processing
- 🗣️ Text-to-speech responses
- 🔊 Voice Activity Detection (VAD)
- 👂 Speech-to-Text using Whisper
- 🗄️ SQLite database integration
- 🌐 Web and system interaction
- 🧩 Modular architecture
- ⚙️ System-level utilities
- 📦 Separated models, configuration, resources and source code

---
📁 Project Structure
alicia/
│
├── archive/          # Archived or experimental code
│
├── config/           # Configuration files
│
├── database/         # Database and persistence layer
│
├── doc/              # Documentation
│
├── models/           # AI / ML models
│
├── notes/             # Development notes and research
│
├── packages/         # Project-specific packages
│
├── resources/        # Images and other resources
│
├── src/              # Main source code
│   ├── model.py
│   ├── stt.py
│   ├── tts.py
│   ├── vad.py
│   ├── system.py
│   └── ...
│
├── test/              # Tests
│
├── .gitignore
├── LICENSE
└── README.md

🔧 Core Components
🎙️ Voice Activity Detection

The VAD layer determines when meaningful speech is being produced.

This prevents Alicia from continuously processing background audio and provides the foundation for a more efficient voice interaction pipeline.

📝 Speech-to-Text

Alicia uses Whisper to convert spoken audio into text.

Speech → Audio → Whisper → Text
🧠 AI Model

The model layer is responsible for understanding the user's request and determining what Alicia should do.

This layer is intentionally separated from the rest of the system so that the underlying model can be changed without rewriting the entire assistant.

🗣️ Text-to-Speech

Once Alicia determines a response, the TTS layer converts the generated text back into speech.

Text → TTS → Audio → User
🗄️ Database

SQLite is used for local persistence.

The database layer is intended to allow Alicia to store and retrieve information required by the assistant.

⚙️ System Tools

Alicia can interact with the local system and perform utility operations such as retrieving system information and interacting with applications or websites.

🚀 Getting Started
1. Clone the repository
git clone https://github.com/kal51411/alicia.git
cd alicia
2. Install dependencies

Install the required Python packages used by the project.

pip install -r requirements.txt

The project is currently under active development, so dependencies may change.

3. Run Alicia
python src/main.py
🛠️ Tech Stack
Technology	Purpose
Python	Core programming language
Whisper	Speech-to-Text
WebRTC VAD	Voice Activity Detection
SoundDevice	Audio input
pyttsx3	Text-to-Speech
SQLite	Local database
NumPy	Audio/data processing
Git & GitHub	Version control