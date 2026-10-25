# AI Code Checker

AI-assisted code review CLI for an early-stage CODE COUNCIL project. It accepts pasted single-file code or a multi-file code bundle, reviews it from role-specific perspectives, and asks a Judge to consolidate findings. It can optionally propose revised code.

## What it does

- Reviews code from eight perspectives, including security, performance, architecture, testing, reliability, maintainability, resource use, and complexity/cost.
- Produces structured findings with severity, location, evidence, impact, and suggested action.
- Lets a Judge summarize agreement, conflicts, priorities, and whether another review round is needed.
- Optionally generates a revised code bundle based on approved changes.

The eight roles are prompts to a Gemini model. By default, they are not eight independent models or human reviewers.

## Requirements

- Python 3.10 or newer
- A Gemini API key

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY`. The default model is `gemini-2.5-flash`. Optional settings can override the agent, judge, and implementation models or adjust review rounds, retries, and concurrency.

## Run

```powershell
python main.py
```

Paste the code or code bundle when prompted, then enter `END` on a new line. Choose whether to generate revised code after reviewing the findings.

## Security and limitations

- The submitted code is sent to the configured Gemini API. Remove API keys, passwords, personal data, and other secrets before submitting code.
- Only submit code you have permission to share with the configured AI provider.
- This is an experimental AI-assisted review tool. Findings may be incorrect or incomplete; verify them before relying on them.
- It is not a penetration test, security certification, or guarantee that code is free of defects.
- This version is a local CLI. It does not yet provide repository upload, GitHub PR integration, a web interface, or customer data management.

## License

MIT. See [LICENSE](LICENSE).
