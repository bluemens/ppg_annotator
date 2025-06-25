# PPG Signal Annotator

A desktop tool for manually annotating photoplethysmography (PPG) signal segments as clean or noisy, designed for high-quality labeling with multi-user support and seamless backend integration.

---

## 🚀 Features

- 🔍 Visual inspection of PPG signals
- 🎚️ Continuous quality annotation via a slider (0.0 to 1.0)
- ⌨️ Keyboard shortcuts for rapid segment labeling
- 🔁 Resume labeling from last segment
- 👥 Multi-annotator support with ID validation
- ☁️ Backend sync for signal loading and annotation upload
- 📁 Signal files in `.parquet` format with timestamps

---

## 🖥️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/ppg-annotator.git
cd ppg-annotator

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt

pip install .

annotator
```

## Backend API (FastAPI)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration Settings 

Store in: 

```bash
~/.annotator_config.json
```

