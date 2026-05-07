# Manhwa-to-YouTube-Recap Pipeline

An automated, local-first pipeline designed to convert vertical Manhwa/Webtoon pages into cinematic YouTube recap videos. This system uses heuristic scene segmentation, PaddleOCR for dialogue extraction, and local LLMs for narrative script generation.

## 🚀 Features
- **Deterministic Slicing**: Automatically segments long vertical images into cinematic scenes.
- **OCR-Aware**: Uses full-page OCR to ensure panels are never cut through dialogue.
- **Local AI**: Powered by Ollama (Llama 3.1) and Coqui XTTS-v2 for private, local execution.
- **High Retention**: Optimized pacing and motion presets for engaging storytelling.
- **Resumable**: Caching layer allows for recovery from interruptions.

---

## 🛠️ Installation Options

### Option A: Docker (Recommended for Portability)
This is the easiest way to get started as it handles all complex AI dependencies (PaddlePaddle, Torch, FFmpeg) automatically.

1. **Install Docker Desktop** on your system.
2. **Clone the repository**:
   ```bash
   git clone https://github.com/MidnightMaverick07/Manhwa-Project.git
   cd Manhwa-Project
   ```
3. **Launch the stack**:
   ```bash
   docker-compose up -d
   ```
4. **Run the pipeline**:
   ```bash
   docker-compose run app --input /app/input/your_manhwa_folder
   ```

---

### Option B: Local Installation (Windows/Linux)
If you prefer running outside of Docker, follow these steps:

#### 1. Prerequisites
- **Python 3.11** (Required for compatibility with AI libs)
- **FFmpeg**: [Download here](https://ffmpeg.org/download.html)
- **Ollama**: [Download here](https://ollama.com/)

#### 2. Set Up Environment
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install stable dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 3. Model Setup
Download the required LLM model via Ollama:
```bash
ollama pull llama3.1:8b
```

---

## 📖 Usage

1. **Prepare Input**: Place your manhwa images or PDFs into the `input/` directory.
2. **Configure**: Adjust `config.yaml` to change models, resolution, or styles.
3. **Execute**:
   ```powershell
   python main.py --input input/your_chapter_folder
   ```

The final video will be generated in the `outputs/` folder.

---

## 📁 Project Structure
- `core/`: Modular engines (OCR, Segmenter, Script, Audio, Video, Timeline).
- `input/`: Raw manhwa images/PDFs.
- `outputs/`: Final MP4 videos and SRT subtitles.
- `temp/`: Intermediate extracted pages.
- `cache/`: OCR and Audio cache for fast re-runs.
- `config.yaml`: Global pipeline settings.

## ⚙️ Configuration
You can customize the cinematic style in `style_profile.yaml` and adjust camera movements in `motion_presets.yaml`.

---

## ⚖️ License
MIT License. Created by MidnightMaverick07.
