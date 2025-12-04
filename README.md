# GitHub Profile Analyzer

A web application that analyzes GitHub profiles and generates comprehensive insights for recruiters and hiring managers. Simply enter a GitHub username, URL, or email to get a detailed developer profile analysis.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Live Demo

**Try it now:** [https://github-profile-analyzer-5rhk.onrender.com](https://github-profile-analyzer-5rhk.onrender.com)

> Note: The demo may take a few seconds to wake up if it hasn't been used recently (free tier cold start).

## Features

- **Smart Input Detection** - Accepts GitHub username, profile URL, or email
- **Developer Score** - 0-100 score based on repos, stars, activity, and engagement
- **Experience Level** - Automatically categorizes as Junior, Mid-Level, Senior, or Expert
- **Tech Stack Analysis** - Visual breakdown of languages with proficiency percentages
- **Activity Patterns** - Most active days/hours, consistency score
- **Focus Areas** - Auto-detected specializations (Web Dev, Data Science, DevOps, etc.)
- **Growth Timeline** - Year-by-year repository creation chart
- **Recruiter Summary** - Auto-generated text summary for quick assessment
- **Caching** - 1-hour cache to minimize API calls for bulk analysis
- **Rate Limit Tracking** - Real-time API usage monitoring

## Quick Start

### 1. Clone and Setup

```bash
cd github-profile-analyzer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure GitHub Token (Recommended)

Without a token, you're limited to 60 API requests/hour. With a token, you get 5,000/hour.

```bash
cp .env.example .env
```

Edit `.env` and add your GitHub token:
```
GITHUB_TOKEN=ghp_your_token_here
```

**To create a token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. No special scopes needed (public data only)
4. Copy and paste into `.env`

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Usage

### Web Interface

1. Enter a GitHub username, URL, or email in the search box
2. Click "Analyze" or press Enter
3. View the comprehensive profile analysis

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze a GitHub profile |
| `/api/rate-limit` | GET | Check API rate limit status |
| `/api/cache/stats` | GET | View cache statistics |
| `/api/cache/clear` | POST | Clear the cache |

#### Example API Call

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "torvalds"}'
```

## Project Structure

```
github-profile-analyzer/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/
│   │   └── analyze.py       # API endpoints
│   ├── services/
│   │   ├── github_service.py    # GitHub API client with caching
│   │   └── analyzer.py          # Profile analysis logic
│   └── models/
│       └── schemas.py       # Pydantic data models
├── static/
│   ├── index.html           # Frontend UI
│   └── js/
│       └── app.js           # Frontend JavaScript
├── requirements.txt
├── .env.example
└── README.md
```

## Analysis Metrics

### Developer Score (0-100)
Calculated from:
- Repository count and quality (0-25 points)
- Total stars earned (0-25 points)
- Language diversity (0-15 points)
- Activity consistency (0-20 points)
- Community engagement (0-15 points)

### Experience Level
- **Junior** - Score < 30, < 1 year on GitHub
- **Mid-Level** - Score 30-50, 1-3 years
- **Senior** - Score 50-70, 3-5 years
- **Expert** - Score 70+, 5+ years with significant contributions

### Focus Areas Detected
- Web Development
- Data Science
- Mobile Development
- Systems Programming
- DevOps
- Backend Development
- Game Development

## Rate Limits

| Mode | Requests/Hour | Profiles/Hour* |
|------|---------------|----------------|
| Without token | 60 | ~2-3 |
| With token | 5,000 | ~200-250 |

*Approximate, depends on number of repositories per profile

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, TailwindCSS, Chart.js
- **API Client**: httpx (async)
- **Data Validation**: Pydantic

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this for your own projects.
