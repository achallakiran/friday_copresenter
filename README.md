# Friday Presenter 🤖🎙️

**Friday** is an intelligent, automated co-presenter designed to act as your "wingman" during town halls, Zoom meetings, and in-person presentations. 

Built out of a personal need to manage strict time limits and presentation fatigue, Friday uses a combination of **local macOS automation** (for speed) and **Large Language Models** (for intelligence) to drive Microsoft PowerPoint, provide live subtitles, keep time, and answer contextual questions.

## 🌟 Key Features

### 🧠 Intelligent Control
* **Voice Navigation:** Navigate slides using natural language (e.g., "Move on," "Go back," "Next").
* **Contextual Jumping:** Jump to specific sections by name (e.g., "Friday, go to the Architecture slide") instead of clicking through linearly.
* **Autopilot ("Take Over"):** Friday can take full control, reading slide narratives naturally using local Neural TTS (Text-to-Speech).

### 🛠 Meeting Utilities
* **Live Subtitles:** A transparent, "Always-on-Top" overlay displaying real-time speech-to-text.
* **Presentation Timer:** A floating countdown timer to keep meetings strictly on schedule.
* **Intelligent Scribe:** Records a transcript of the session and generates structured summaries using GenAI.
* **Documentation:** Captures photos of the session via webcam automatically.

### ⚙️ Hybrid Architecture
* **Local-First:** Basic commands, TTS, and slide automation run locally on macOS for zero latency.
* **LLM-Powered:** Complex tasks (Summarization, "Explain this slide") are routed to Azure OpenAI to optimize costs and tokens.

---

## 📋 Prerequisites

* **Operating System:** macOS (Required for AppleScript automation).
* **Software:** Microsoft PowerPoint.
* **Hardware:** Microphone & Webcam.
* **Tools:** * Python 3.8+
    * [Homebrew](https://brew.sh/) (for installing system tools).

---

## 🚀 Installation & Setup

### 1. System Dependencies
Friday uses `imagesnap` to take photos and `portaudio` for microphone access.
```bash
brew install imagesnap portaudio
