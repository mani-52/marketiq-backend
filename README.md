# MarketIQ Backend v3.0

Real-time market intelligence API. 100% real data — no fabrication.

## 🚀 Quick Start

```bash
pip install -r requirements.txt
# Copy .env.example → .env and fill in your keys
uvicorn app.main:app --reload --port 8000
```

## 🔑 Environment Variables

| Key | Required | Description |
|-----|----------|-------------|
| `TAVILY_API_KEY` | ✅ | Get free at https://tavily.com |
| `JWT_SECRET` | ✅ | Random secret for JWT signing |
| `SMTP_USER` | Optional | Gmail address for email notifications |
| `SMTP_PASSWORD` | Optional | Gmail App Password |
| `GOOGLE_CLIENT_ID` | Optional | For Google OAuth |

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Backend health check |
| `/analyze` | GET | Analyze company news (`?company=Apple&days=7`) |
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Login with email+password |
| `/auth/google` | POST | Exchange Google token for JWT |
| `/auth/me` | GET | Get current user (requires Bearer token) |
| `/notifications` | GET/POST | List / create reminders |
| `/notifications/{id}` | DELETE | Delete a reminder |
| `/notifications/settings` | GET/PUT | Email notification preferences |
| `/notifications/log` | GET | Sent emails log |
| `/domain-matrix` | GET | Full domain classification matrix |

## 🔔 Notification Engine

- Users set reminders with a title, optional company, and fire time (exact datetime or relative offset)
- Supports daily / weekly repeat
- Background scheduler checks every 30s and sends emails via SMTP
- Emails are sent to the user's registered email address
- Master switch in `/notifications/settings`

## 📊 Domain Classification Matrix

9 domains × 5 dimensions:
- **Risk Weight** — how much this domain signals risk
- **Innovation Weight** — innovation signal strength
- **Volatility Weight** — how volatile/fast-moving
- **Growth Signal** — growth indicator strength
- **Sentiment Bias** — typical sentiment polarity

## 📅 Days Parameter

`/analyze?company=Apple&days=7` — days range: **1–30** (user-specified)

## ⚙️ Architecture

```
app/
├── main.py              ← FastAPI app, all routers registered
├── config.py            ← Settings (Tavily, JWT, SMTP, Google OAuth)
├── routes/
│   ├── analysis.py      ← /analyze endpoint
│   ├── auth.py          ← /auth/* JWT auth + Google OAuth
│   ├── notifications.py ← /notifications/* + background scheduler
│   ├── domain_matrix.py ← /domain-matrix endpoint
│   └── health.py        ← /health
├── services/
│   ├── email_service.py ← SMTP email sending + templates
│   ├── tavily_service.py
│   └── intelligence_service.py
└── ml/
    ├── training_data.py ← Domain keywords + classification matrix
    └── domain_classifier.py
```
