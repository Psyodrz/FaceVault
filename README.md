# 🛡️ FaceVault: Neural Intelligence Platform

[![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?style=flat&logo=vercel)](https://vercel.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?style=flat&logo=opencv)](https://opencv.org)

**FaceVault** is a production-grade facial intelligence platform engineered for real-time surveillance, threat detection, and personnel registry management. Built on a high-performance ASGI stack with a premium glassmorphic interface.

---

## 🚀 Instant Deployment

### 1. Backend (FastAPI + ML Engine)
Deploy the neural engine to **Cloud Run**, **Render**, or **Railway** using the provided `Dockerfile`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 2. Frontend (React 18 + Vite)
The frontend is optimized for **Vercel**. 

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FPsyodrz%2FFaceVault)

---

## 🧠 Core Intelligence
- **YuNet + SFace Pipeline**: High-speed ONNX-optimized detection and recognition.
- **Environmental Ergonomics**: Integrated "Sentinel Light" and "Sentinel Dark" modes.
- **Tactical Telemetry**: Real-time WebSocket streaming for millisecond-latency recognition.
- **Security Console**: RBAC-gated access control with forensic audit trails.

## 🛠️ Tech Stack
- **Core**: Python 3.10+, FastAPI, SQLAlchemy.
- **ML Engine**: OpenCV DNN, YuNet (Detection), SFace (Recognition).
- **Frontend**: React 18, Vite, Lucide, Vanilla CSS (Premium Glassmorphism).
- **Deployment**: Docker, Vercel, Cloud Run.

## 📦 Installation (Local)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development)

### Quick Start
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Psyodrz/FaceVault.git
   cd FaceVault
   ```

2. **Initialize Backend**:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

3. **Initialize Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🛡️ Governance & Privacy
FaceVault is designed with **Local Sovereignty** in mind. All facial signatures and feature vectors are stored locally in the `face_vault.db` and `facevault_features.pkl` files. No biometric data is ever transmitted to external cloud providers.

---
Created by **Psyodrz** • [FaceVault Sentinel 1.0]
