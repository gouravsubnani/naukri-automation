# Naukri.com Resume Automation

Automatically uploads your resume and updates your profile headline on Naukri.com every day at 9:00 AM. Keeps your profile fresh and visible to recruiters.

## What It Does

1. **Logs in** to your Naukri.com account
2. **Uploads your resume** — refreshes the "last updated" timestamp so recruiters see you as active
3. **Updates your headline** — generates a new keyword-rich headline daily using terms like Data Engineer, STL, SnapLogic, Developer, ETL, Python, SQL, and more

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

### 2. Install Python dependencies

```bash
# Windows
pip install -r requirements.txt

# macOS / Linux
pip3 install -r requirements.txt
```

### 3. Configure your credentials

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in:
- `NAUKRI_EMAIL` — your Naukri login email
- `NAUKRI_PASSWORD` — your Naukri password
- `RESUME_PATH` — full path to your resume PDF/DOC file

Example paths:
```
# Windows
RESUME_PATH=C:/Users/yourname/Documents/MyResume.pdf

# macOS
RESUME_PATH=/Users/yourname/Documents/MyResume.pdf

# Linux
RESUME_PATH=/home/yourname/Documents/MyResume.pdf
```

## Usage

### Run once (test it out)

```bash
python scheduler.py --now       # Windows
python3 scheduler.py --now      # macOS / Linux
```

### Run the scheduler (keeps running in background)

```bash
python scheduler.py             # Windows
python3 scheduler.py            # macOS / Linux
```

This starts a loop that triggers the automation at 09:00 AM daily. Keep the terminal open or run it as a background process.

---

## Scheduling (Run Daily at 9:00 AM)

### GitHub Actions — Cloud (recommended, no laptop needed)

The repo includes a GitHub Actions workflow that runs daily at 9:00 AM IST in the cloud. Your laptop can be off, asleep, or closed — it doesn't matter.

**One-time setup:**

1. **Encode your resume as base64.** Run this in your terminal:

   ```bash
   # macOS / Linux
   base64 -i /path/to/MyResume.pdf | pbcopy    # copies to clipboard (macOS)
   base64 /path/to/MyResume.pdf                 # prints to terminal (Linux)

   # Windows PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\MyResume.pdf")) | Set-Clipboard
   ```

2. **Add these three secrets** to your GitHub repo:

   Go to **repo → Settings → Secrets and variables → Actions → New repository secret** and add:

   | Secret name | Value |
   |---|---|
   | `NAUKRI_EMAIL` | Your Naukri login email |
   | `NAUKRI_PASSWORD` | Your Naukri password |
   | `RESUME_BASE64` | The base64 string of your resume (from step 1) |

3. **Done!** The workflow runs automatically every day at 9:00 AM IST.

**To run it manually:** Go to **Actions → Naukri Daily Automation → Run workflow**.

**To update your resume:** Re-encode the new file as base64 and update the `RESUME_BASE64` secret.

Logs are saved as downloadable artifacts for 7 days after each run.

---

### Windows — Task Scheduler

The most reliable way on Windows. Works even after reboots.

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

Replace `/Users/yourname` with your actual home directory (`echo $HOME`).

Verify:
```bash
crontab -l
```

**Important — macOS permissions:**

macOS blocks cron from controlling apps by default. Grant access:

1. Go to **System Settings → Privacy & Security → Full Disk Access**
2. Click **+** and add `/usr/sbin/cron` (press Cmd+Shift+G to type the path)

Without this, cron jobs may silently fail.

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
sudo systemctl enable cron
sudo systemctl start cron
```

---

## File Structure

```
naukri-automation/
├── .github/workflows/
│   └── naukri-daily.yml     # GitHub Actions workflow (daily cloud run)
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
| Task Scheduler not running (Windows) | Make sure Python is in your system PATH. Check Task Scheduler history for errors. |
| Cron not running (macOS) | Grant Full Disk Access to `/usr/sbin/cron` in System Settings. |
| Cron not running (Linux) | Run `sudo systemctl start cron` and check `cron.log` for errors. |

## Notes

- Naukri may change their website structure — if selectors break, the script logs detailed errors to `naukri_automation.log`.
- The script runs Chrome in headless mode (no visible browser window).
- Each day generates a deterministic headline, so running multiple times on the same day won't keep changing it.
- Your credentials are stored locally in `.env` and never transmitted anywhere except to Naukri's login page.
