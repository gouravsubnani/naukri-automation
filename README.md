# Naukri.com Resume Automation

Automatically uploads your resume and updates your profile headline on Naukri.com every day at 9:00 AM. Keeps your profile fresh and visible to recruiters.

## What It Does

1. **Logs in** to your Naukri.com account
2. **Uploads your resume** — refreshes the "last updated" timestamp so recruiters see you as active
3. **Updates your headline** — generates a new keyword-rich headline daily using terms like Data Engineer, STL, SnapLogic, Developer, ETL, Python, SQL, and more

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your credentials

```bash
copy .env.example .env
```

Open `.env` and fill in:
- `NAUKRI_EMAIL` — your Naukri login email
- `NAUKRI_PASSWORD` — your Naukri password
- `RESUME_PATH` — full path to your resume PDF/DOC file

### 3. Install Chrome

The script uses Chrome in headless mode. Make sure Google Chrome is installed on your machine. The ChromeDriver is downloaded automatically by `webdriver-manager`.

## Usage

### Run once (test it out)

```bash
python scheduler.py --now
```

### Run the scheduler (keeps running in background)

```bash
python scheduler.py
```

This starts a loop that triggers the automation at 09:00 AM daily. Keep the terminal open (or run it as a background process).

### Best option: Windows Task Scheduler (recommended)

This is the most reliable way to run daily — it works even if you restart your PC.

**Option A — Use the provided batch file:**

1. Right-click `setup_task_scheduler.bat` and select **Run as administrator**
2. Done! The task is created and will run daily at 9:00 AM.

**Option B — Manual setup:**

1. Open **Task Scheduler** (search in Start Menu)
2. Click **Create Basic Task**
3. Name it: `NaukriResumeAutomation`
4. Trigger: **Daily** at **9:00 AM**
5. Action: **Start a program**
   - Program: `python`
   - Arguments: `"C:\Users\gousubna\naukri-automation\scheduler.py" --now`
   - Start in: `C:\Users\gousubna\naukri-automation`
6. Check **Open the Properties dialog** and enable **Run whether user is logged on or not**
7. Finish

## File Structure

```
naukri-automation/
├── naukri_automation.py     # Main automation (login, upload, headline update)
├── headline_generator.py    # Generates fresh daily headlines with keywords
├── scheduler.py             # Scheduler (daily at 9 AM) or one-shot with --now
├── setup_task_scheduler.bat # One-click Windows Task Scheduler setup
├── requirements.txt         # Python dependencies
├── .env.example             # Template for credentials
├── .env                     # Your actual credentials (not committed)
├── .gitignore               # Keeps secrets and logs out of git
└── README.md                # This file
```

## Customization

### Change the schedule time

Edit `SCHEDULED_TIME` in `scheduler.py`:

```python
SCHEDULED_TIME = "09:00"  # Change to any 24-hour time, e.g. "08:30"
```

### Change headline keywords

Edit the keyword lists in `headline_generator.py`:

- `CORE_KEYWORDS` — always included in rotation (Data Engineer, STL, SnapLogic, Developer)
- `SKILL_KEYWORDS` — additional skills mixed in (ETL, Python, SQL, AWS, etc.)
- `HEADLINE_TEMPLATES` — the sentence patterns used to build headlines

### Preview today's headline

```bash
python headline_generator.py
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Login fails | Check `.env` credentials. If Naukri asks for CAPTCHA/OTP, run once in non-headless mode (remove `--headless=new` in the script) to handle it manually. |
| Resume upload fails | Make sure `RESUME_PATH` in `.env` points to an existing PDF/DOC file. |
| Chrome not found | Install Google Chrome. The driver is managed automatically. |
| Task Scheduler not running | Make sure Python is in your system PATH. Check Task Scheduler history for errors. |

## Notes

- Naukri may change their website structure — if selectors break, the script logs detailed errors to `naukri_automation.log`.
- The script runs Chrome in headless mode (no visible browser window).
- Each day generates a deterministic headline, so running multiple times on the same day won't keep changing it.
- Your credentials are stored locally in `.env` and never transmitted anywhere except to Naukri's login page.
