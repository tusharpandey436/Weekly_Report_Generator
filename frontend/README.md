# AI Weekly Analyst — React Frontend

A dark-themed, production-grade React frontend for the AI Weekly Analyst FastAPI backend.

## Stack

- **React 18** + Vite
- **Fonts**: Syne (headings) + DM Mono (body)
- **No UI library** — fully custom CSS with CSS variables
- **API**: Connects to FastAPI backend at `http://localhost:8000`

## Project Structure

```
src/
├── App.jsx                     # Root layout + state
├── main.jsx                    # Entry point
├── index.css                   # All styles (CSS variables, dark theme)
└── components/
    ├── UploadPanel.jsx          # File drop zone + date pickers
    ├── ResultsDashboard.jsx     # Week selector + main view
    ├── WeekCard.jsx             # AI summary + peak/trend cards
    └── MetricsSummary.jsx       # Raw metrics table
```

## Quick Start

```bash
npm install
npm run dev
# → http://localhost:5173
```

Make sure the FastAPI backend is running on port 8000 first:
```bash
uvicorn ai_weekly_analyst.main:app --reload --port 8000
```

The Vite dev server proxies `/api/*` → `http://localhost:8000` automatically.

## Features

- **Drag & drop** `.xlsx` upload with file validation
- **Date range picker** with start/end inputs
- **Week sidebar** to switch between analysed weeks
- **AI summary panel** with animated indicator
- **Peak day** and **trend comparison** insight cards
- **Raw metrics table** with sum + daily mean per column
- Full **error handling** with styled error banners
