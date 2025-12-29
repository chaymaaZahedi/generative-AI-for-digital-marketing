# 🤖 AI Generative - LinkedIn Intelligent Agent

**A Powerful, Autonomous AI Agent for LinkedIn Scraping, Analysis, and Outreach.**

This project is a comprehensive solution for automating LinkedIn workflows. It combines advanced web scraping (using Playwright and MCP), AI-driven data enrichment (Claude-Sonnet), and an intelligent database system to help you find, analyze, and connect with professionals.

---

## 🚀 Key Features

### 1. 🔍 Deep LinkedIn Scraping (MCP Server)
- **Direct Search Extraction**: Bypasses standard API limits by simulating real user behavior to extract profiles directly from LinkedIn search results.
- **Multi-Strategy Selectors**: Uses robust, redundant CSS selectors to ensure data is captured even if LinkedIn changes its DOM structure.
- **Smart Pagination**: Automatically navigates through multiple pages of search results.
- **Session Management**: Handles login sessions securely to maintain access.

### 2. 🧠 AI-Powered Analysis & Enrichment
- **Gender Detection**: Uses AI to infer gender based on profile names and images.
- **Age Estimation**: Analyzes education history (graduation years) to estimate the candidate's age.
- **Education Parsing**: Structured extraction of schools, degrees, and dates.

### 3. 🗄️ Intelligent Database & Filtering
- **Centralized Storage**: Saves all extracted profiles to a SQLite database (`linkedin_profiles.db`).
- **Advanced Filtering**: Filter candidates by:
    - Keywords (Position, Skills)
    - Location
    - Age Range
    - Gender
    - Education
- **Export**: Download filtered results as CSV for external use.

### 4. 📧 Email Campaign Manager
- **Template Management**: Create and save custom email templates.
- **Campaign Automation**: Send personalized emails to selected candidates directly from the dashboard.

### 5. 🤖 Autonomous Agent(DB and Email Campaign)
- **Goal-Oriented Workflow**: Give the agent a high-level goal (e.g., "Find 10 Data Scientists in Paris and save them"), and it will orchestrate the necessary tools to achieve it.
- **Self-Correcting**: The agent can retry steps and adjust its approach if it encounters errors.

---

## 📂 Repository Structure

This project is built as a modular **FastAPI** application with a separate **MCP (Model Context Protocol)** server for browser automation.

```
AI_Generative/
├── app/
│   ├── main.py                 # 🚀 FastAPI Entrypoint
│   ├── config.py               # ⚙️ Configuration & Env Variables
│   ├── routes/                 # 🌐 API Endpoints & UI Routes
│   │   ├── scraper.py          # -> Scraper UI & Trigger
│   │   ├── filter.py           # -> Database Search & Filtering
│   │   ├── agent.py            # -> Autonomous Agent Interface
│   │   └── email_campaign.py   # -> Email Template & Sending Logic
│   ├── services/               # 🧠 Business Logic
│   │   ├── linkedin_service.py # -> Orchestrates MCP & AI Tools
│   │   └── db_service.py       # -> Database Operations
│   ├── models/                 # 📦 Pydantic Data Models
│   └── templates/              # 🎨 Jinja2 HTML Templates (UI)
├── linkedin_mcp_server.py      # 🖥️ MCP Server (Playwright Browser Control)
├── linkedin_profiles.db        # 🗄️ SQLite Database
├── requirements.txt            # 📦 Python Dependencies
└── README.md                   # 📖 Documentation
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Browser Automation**: Playwright, Model Context Protocol (MCP)
- **AI/LLM**: Claude-Sonnet
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Jinja2 Templates
- **Process Management**: Uvicorn

---

## ⚡ Prerequisites

1.  **Python 3.10+** installed.
2.  **Playwright** browsers installed:
    ```bash
    playwright install
    ```
3.  **Claude Credentials**:
    - `ANTHROPIC_API_KEY`
    - `LINKEDIN_EMAIL`
    - `LINKEDIN_PASSWORD`

4.  **LinkedIn Account**:
    - A valid LinkedIn email and password (stored in `.env` or `config.py`).

---

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd AI_Generative
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment**:
    Create a `.env` file or update `app/config.py` with your credentials.

---

## 🏃‍♂️ Running the Application
0.  **Log in Linkedin via Chrome with your credentials** 
1.  **Start the FastAPI Server**:
    This will start the web application and the API.
    ```bash
    uvicorn app.main:app --reload
    ```

2.  **Access the UI**:
    Open your browser and navigate to:
    👉 **http://localhost:8000**

---

## 📖 Usage Guide

### 1. Scraping Profiles
- Go to the **LinkedIn Scraper** tab.
- Enter a **Job Title** (e.g., "Software Engineer") and **Location**.
- Click **Start Scraping**.
- Watch the logs as the agent logs in, searches, and extracts data.

### 2. Filtering & Exporting
- Go to the **Intelligent Extraction** tab.
- Use the sidebar filters to narrow down your search (e.g., "Show only Senior Developers in London").
- Click **Export to CSV** to download your list.

### 3. Email Campaigns
- Go to the **Email Campaign** tab.
- Select the candidates you want to contact.
- Choose or write an email template.
- Click **Send Campaign**.

---

## 🔌 API Endpoints

The application exposes several RESTful endpoints. View the full interactive documentation at:
**http://localhost:8000/docs**

- `POST /scrape/linkedin`: Trigger the scraper.
- `GET /api/profiles`: Retrieve profiles with filters.
- `POST /api/agent/run`: Execute an autonomous agent task.
