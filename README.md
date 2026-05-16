# 🏟️ Agentic IPL Digital Stadium

A premium, high-performance "Digital Stadium" dashboard designed for the **Agentic Premier League Hackathon**. This project combines real-time data scraping with multiple Agentic AI models to provide tactical insights, win probabilities, and interactive gamification for IPL 2026.

---

## 🚀 Key Features

### 1. Fan Engagement (Challenge 1)
- **🧠 AI Live Commentary**: Real-time witty updates with dynamic "Manifesting" tickers.
- **📊 Win Probability Index**: Live-syncing probability metrics powered by Gemini 1.5.
- **⚡ Tactical Strategy Agent**: Real-time bowling suggestions based on live match context.

### 2. Gamification (Challenge 2)
- **📈 XP & Leveling System**: Integrated progression engine that rewards user interactions.
- **🏅 Interactive Badges**: Unlock milestones like "Rookie", "Strategic Brain", and "Stadium Legend".
- **⚽ Squad XI Generator**: AI-driven Playing XI builder with built-in roster validation rules.

---

## 📂 Repository Structure

```bash
├── backend/            # Flask API, AI Agents & Scraping Logic
├── frontend/           # React + Vite Dashboard (Premium UI)
├── README.md           # Master Project Documentation
└── .gitignore          # Global Security rules
```

---

## 🛠️ Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Vanilla CSS (High-End Aesthetics).
- **Backend**: Flask (Python), Gunicorn, Google Gemini 1.5 Flash API.
- **Deployment**: Render (Backend), Vercel (Frontend).

---

## 🏁 Quick Start

### 1. Backend Hub (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
*Live at: [https://ipl-2026-api.onrender.com](https://ipl-2026-api.onrender.com)*

### 2. Frontend Dashboard (React)
```bash
cd frontend
npm install
npm run dev
```

---

## 🛡️ Environment Variables
Ensure you have the following in your `.env` files:
- `VITE_GEMINI_API_KEY`: Your Google AI Studio API Key.
- `VITE_API_BASE_URL`: Pointer to your backend (local or production).

---

## 📜 License
Released under the [MIT License](LICENSE). 

> [!NOTE]  
> This project is designed for the Agentic Premier League Hackathon. All cricket data is scraped for educational and competition purposes.
