# PR Agent

PR Agent is an automated code review tool powered by LLMs. It analyzes Pull Requests, identifies issues (Logic, Security, Performance, Readability), and provides actionable suggestions.

## Features

- **Automated Analysis**: Fetches PR diffs and analyzes them using a multi-agent graph workflow.
- **Categorized Issues**: Identifies issues across multiple categories:
  - Logic
  - Security
  - Performance
  - Readability
- **Severity Levels**: Classifies issues by severity (Critical, High, Medium, Low) with visual indicators.
- **Inline Comments**:
  - **Manual**: Post individual issues as inline comments directly to GitHub with a single click.
  - **Automatic**: (Optional) Can be configured to automatically post all issues.
- **Interactive UI**: A modern Next.js frontend to trigger reviews and view results.

## Architecture

- **Backend**: Python (FastAPI) with LangGraph for the agent workflow.
- **Frontend**: TypeScript (Next.js) with Tailwind CSS.
- **AI**: Uses LangChain and OpenAI (or compatible LLMs).

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- GitHub Token (with repo permissions)
- Gemini API Key

### Backend

1.  Navigate to the root directory.
2.  Create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up environment variables in `.env`:
    ```env
    GITHUB_TOKEN=your_github_token
    GOOGLE_API_KEY=your_gemini_api_key
    ```
5.  Run the server:
    ```bash
    python -m src.pr_agent.api.main
    ```

### Frontend

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
4.  Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1.  Start both the backend and frontend servers.
2.  Enter a GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`) in the frontend.
3.  Click **Analyze**.
4.  Review the identified issues.
5.  Click **Post Comment** on any issue to publish it to GitHub.
