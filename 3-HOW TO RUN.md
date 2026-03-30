# How To Run

## Last Updated: 2026-03-29 18:21:00

---

## Quick Start (5 Steps)

### Step 1: Configure API Keys
Edit the `.env` file in the project root:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
NOTION_TOKEN=your_actual_notion_token_here
DATABASE_ID=33109f62-78d4-80f6-9da5-dad7b6591885
```

### Step 2: Start the Auto-Watcher
```powershell
python auto_watcher.py
```
Keep this running in a terminal window.

### Step 3: Capture Your Trade Thoughts
Create a new text file in `trading_notes/` folder. You can:
- Open Notepad with Right Ctrl hotkey
- Type or dictate your thoughts
- Save the file with any name

### Step 4: Watch the Magic
The auto-watcher will:
1. Detect the new file
2. Send it to Groq AI for parsing
3. Create a new entry in your Notion trading journal
4. Archive the processed file

### Step 5: Check Your Notion
Open your Notion database and verify the new entry was created with all your voice-captured properties.

---

## Voice Transcript Format

Your text files should follow this pattern for best results:

```
[Trade Entry - 2026-03-29 18:00]

mood: calm
setup: breakout
anchor: hammer
level: blue level
note: testing the system
```

### Supported Keywords

| Pattern | Maps To | Example |
|---------|---------|---------|
| `mood: [word]` | Internal_State | `mood: zen`, `mood: anxious` |
| `setup: [word]` | M1_Confirm | `setup: breakout` (sets M1_Confirm: true) |
| `anchor: [word]` | M5_Anchor | `anchor: hammer`, `anchor: engulfing` |
| `level: [word]` | Level_Type | `level: blue level`, `level: red level` |
| `note: [text]` | Notes | Free-form notes |

### Quick Keywords (Single Words)

You can also use single words:
- `hammer`, `shooting star`, `engulfing` → M5_Anchor
- `blue`, `red`, `LIS`, `BKBrown` → Level_Type
- `calm`, `zen`, `anxious`, `FOMO`, `revenge` → Internal_State
- `breakout`, `confirmed` → M1_Confirm: true

---

## File System Layout

```
PROJECT_ROOT/
├── auto_watcher.py          # Main script (run this)
├── token_tracker.py         # Token usage tracking
├── .env                     # API keys (NOT committed to Git)
├── trading_notes/           # Drop your voice transcripts here
│   ├── (your files...)
│   └── processed/           # Archive of processed files
├── screenshots/             # Trade screenshots
├── docs - Cam/              # Design documentation
└── _bmad/                   # Agent workflows

```

---

## Running Modes

### Development Mode (Verbose Logging)
```powershell
$env:DEBUG="true"
python auto_watcher.py
```

### Production Mode (Silent)
```powershell
python auto_watcher.py > $null 2>&1
```

### Test Mode (Dry Run)
```powershell
$env:DRY_RUN="true"
python auto_watcher.py
```

---

## Troubleshooting

### "API key not found"
→ Edit `.env` file and add your actual API keys

### "Notion database not found"
→ Verify DATABASE_ID is correct in `.env`
→ Check Notion database sharing settings

### "No files processed"
→ Make sure files are .txt format
→ Check files are in `trading_notes/` folder (not subfolders)
→ Verify auto_watcher.py is running

### "Permission denied"
→ Run PowerShell as Administrator
→ Check file permissions on trading_notes/ folder

---

## Monitoring Token Usage

Check how much you've used:
```powershell
python -c "from token_tracker import get_usage_summary; print(get_usage_summary())"
```

Token data is stored in `token_usage.json`:
```json
{
  "daily": {"prompt": 1500, "completion": 300},
  "monthly": {"prompt": 45000, "completion": 9000},
  "all_time": {"prompt": 450000, "completion": 90000},
  "last_reset": "2026-03-01"
}
```

---

## Keyboard Shortcut (Optional)

To set up Right Ctrl + N for quick Notepad access:
1. Open Windows Settings → Keyboard Shortcuts
2. Create a new shortcut for Notepad
3. Assign Right Ctrl + N

---

## Stopping the Watcher

Press `Ctrl + C` in the terminal running auto_watcher.py

---

## GitHub Repository

- **Remote**: https://github.com/alesiosc/TRADING-JOURNAL-WITH-VOICE
- **Status**: Clean, no secrets exposed
- **Last Updated**: 2026-03-29