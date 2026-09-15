# Naukri.com Resume Automation

Automatically uploads your resume and updates your profile headline on Naukri.com every day at 9:00 AM. Keeps your profile fresh and visible to recruiters.

## What It Does

1. **Uploads your resume** — refreshes the "last updated" timestamp so recruiters see you as active
2. **Updates your headline** — generates a new keyword-rich headline daily using terms like Data Engineer, STL, SnapLogic, Developer, ETL, Python, SQL, and more

## How Authentication Works

Naukri requires OTP verification when logging in from a new location (like a cloud server). To get around this, the script uses **cookie-based authentication**:

1. You log in once manually on your machine (with OTP)
2. The cookies are saved and reused for all future automated runs
3. Cookies typically last **30+ days** — you only need to refresh them once a month

## Prerequisites

- **Python 3.8+**
- **Google Chrome** installed ([download here](https://www.google.com/chrome/))
- ChromeDriver is downloaded automatically by `webdriver-manager`

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/gouravsubnani/naukri-automation.git
cd naukri-automation
```

### 2. Install dependencies

```bash
# Windows
pip install -r requirements.txt

# macOS / Linux
pip3 install -r requirements.txt
```

### 3. Export your Naukri cookies (one-time)

```bash
python export_cookies.py
```

This opens a Chrome window. Log in to Naukri normally (email, password, OTP). Once you're on the dashboard, come back to the terminal and press **Enter**. The cookies are saved to `naukri_cookies.json` and the JSON string is printed for GitHub Actions.

### 4. Configure your resume path

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and set your resume path:
```
# Windows
RESUME_PATH=C:/Users/yourname/Documents/MyResume.pdf

# macOS
RESUME_PATH=/Users/yourname/Documents/MyResume.pdf
```

### 5. Test it

```bash
python scheduler.py --now
```

## Scheduling (Run Daily at 9:00 AM)

### GitHub Actions — Cloud (recommended, no laptop needed)

The repo includes a GitHub Actions workflow that runs daily at 9:00 AM IST. Your laptop can be off.

**One-time setup:**

1. Run `python export_cookies.py` on your machine and log in
2. The script prints a JSON string at the end — **copy it**
3. Go to your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**
4. Add one secret:

   | Secret name | Value |
   |---|---|
   | `NAUKRI_COOKIES` | The JSON string from step 2 |

5. **Done!** The workflow runs automatically every day at 9:00 AM IST.

**To run it manually:** Go to **Actions → Naukri Daily Automation → Run workflow**.

**To update your resume:** Replace the file at `resume/Gourav_Resume_DataEngineer.pdf` in the repo and push.

**When cookies expire (~30 days):** Run `python export_cookies.py` again and update the `NAUKRI_COOKIES` secret with the new JSON string.

Logs and screenshots are saved as downloadable artifacts for 7 days after each run.

---

### Windows — Task Scheduler

**Option A — Use the provided batch file:**

1. Right-click `setup_task_scheduler.bat` → **Run as administrator**
2. Done! The task runs daily at 9:00 AM.

**Option B — Manual setup:**

1. Open **Task Scheduler** (search in Start Menu)
2. Click **Create Basic Task**
3. Name: `NaukriResumeAutomation`
4. Trigger: **Daily** at **9:00 AM**
5. Action: **Start a program**
   - Program: `python`
   - Arguments: `"C:\Users\yourname\naukri-automation\scheduler.py" --now`
   - Start in: `C:\Users\yourname\naukri-automation`
6. Enable **Run whether user is logged on or not**
7. Finish

**Verify / Remove:**
```powershell
schtasks /query /tn "NaukriResumeAutomation"          # verify
schtasks /delete /tn "NaukriResumeAutomation" /f       # remove
```

---

### macOS — Cron Job

```bash
crontab -e
```

Add this line:

```
0 9 * * * cd /Users/yourname/naukri-automation && /usr/bin/python3 scheduler.py --now >> /Users/yourname/naukri-automation/cron.log 2>&1
```

**Important — macOS permissions:**
Go to **System Settings → Privacy & Security → Full Disk Access** and add `/usr/sbin/cron`.

---

### Linux — Cron Job

```bash
crontab -e
```

Add this line:

```
0 9 * * * cd /home/yourname/naukri-automation && /usr/bin/python3 scheduler.py --now >> /home/yourname/naukri-automation/cron.log 2>&1
```

Make sure cron is running:
```bash
sudo systemctl enable cron && sudo systemctl start cron
```

---

## File Structure

```
naukri-automation/
├── .github/workflows/
│   └── naukri-daily.yml       # GitHub Actions workflow (daily cloud run)
├── resume/
│   └── Gourav_Resume_*.pdf    # Your resume file (committed to repo)
├── naukri_automation.py       # Main automation (cookie login, upload, headline)
├── export_cookies.py          # One-time cookie exporter (run locally)
├── headline_generator.py      # Generates fresh daily headlines with keywords
├── scheduler.py               # Scheduler (daily at 9 AM) or one-shot with --now
├── setup_task_scheduler.bat   # One-click Windows Task Scheduler setup
├── requirements.txt           # Python dependencies
├── .env.example               # Template for resume path config
├── .env                       # Your local config (not committed)
├── naukri_cookies.json        # Your saved cookies (not committed)
├── .gitignore                 # Keeps secrets, cookies, and logs out of git
└── README.md                  # This file
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
| Cookie login failed | Cookies expired. Run `python export_cookies.py` again and update the GitHub secret. |
| Resume upload fails | Make sure `RESUME_PATH` in `.env` points to an existing PDF/DOC file. |
| Chrome not found | Install Google Chrome. The driver is managed automatically. |
| Task Scheduler not running (Windows) | Make sure Python is in your system PATH. |
| Cron not running (macOS) | Grant Full Disk Access to `/usr/sbin/cron`. |
| Cron not running (Linux) | Run `sudo systemctl start cron` and check `cron.log`. |
| Screenshots show unexpected page | Download the `screenshots` artifact from GitHub Actions to debug. |

## Notes

- Naukri may change their website structure — if selectors break, the script logs errors and saves screenshots to `screenshots/`.
- The script runs Chrome in headless mode (no visible browser window).
- Each day generates a deterministic headline — running multiple times on the same day produces the same headline.
- Cookies and credentials are stored locally or in GitHub Secrets — never committed to git.
- Cookies typically last 30+ days. When they expire, just run `export_cookies.py` again.
