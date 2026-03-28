# How To Run

## Last Updated: 2026-03-28 19:50:00

This document contains instructions for running and using the Trading Journal with Voice system.

---

## Current Project Status

This project is a **trading journal system** that uses:
- **Zavi** (zavivoice.com) - Voice assistant for hands-free data entry
- **Notion** - Database for storing trading journal entries
- **Custom Python Scripts** - Auto-watcher and automation tools
- **Groq API** - AI processing for voice transcript parsing
- **Custom M5/M1 Strategy** - Trading methodology being tracked

---

## Running the System

### Option 1: Auto-Watcher (Recommended)

The auto-watcher monitors a folder and automatically processes voice transcripts to Notion.

1. **Install Dependencies:**
   ```powershell
   pip install watchdog groq notion-client
   ```

2. **Run the Auto-Watcher:**
   ```powershell
   python auto_watcher.py
   ```

3. **Using the System:**
   - Press Right Ctrl to open Notepad
   - Dictate your trading thoughts
   - Save the file as .txt in the `trading_notes` folder
   - The auto-watcher will process it and create a Notion entry

### Option 2: Zavi Setup (Voice Assistant)

- Download Zavi from zavivoice.com
- Configure Notion integration in Zavi app
- Set up the Voice-to-Structure Dictionary in Zavi's agent settings

### Notion Database Setup

- Open Notion and navigate to database: `33109f62-78d4-80f6-9da5-dad7b6591885`
- Database should have the following properties:
  - **Strategy**: M5 Anchor, M1 Confirm, Level Type, Setup Quality
  - **Mindset**: Internal State, Impulse Level, Patience Grade, Zavi Narrative
  - **Outcome**: Discipline Score (formula)

---

## Daily Workflow

### With Auto-Watcher
1. **Start**: Run `python auto_watcher.py` in terminal
2. **During Trading**: Press Right Ctrl → Notepad opens → Type thoughts → Save to trading_notes/
3. **Auto-Processing**: Script detects new file → Parses with Groq → Creates Notion entry
4. **View**: Check Notion database for new entries

### Traditional Zavi Flow
- **08:30 AM** - Pre-Market: Click "Start Session" button, use Zavi to dictate daily goals
- **Trading Hours** - Use Zavi voice commands to log trades
- **04:30 PM** - Post-Market: Voice to Zavi for reflection

---

## Voice Commands (for Zavi)

Use these trigger phrases with Zavi:

- **Pre-Trade**: "Zavi, record to Zavi Narrative: [your thoughts]"
- **During Trade**: "Zavi, add to Internal Narrative: [live updates]"
- **Post-Trade**: "Zavi, set Patience Grade to [A/C/F]"

---

## Important Notes

- The project follows "Simple, voice-first, easiest to use" principle
- Keep voice entries short and natural
- Use the Discipline Score to track your trading discipline
- Review weekly using the Spoken Weekly Brief feature

---

## Token Usage Tracking

The system tracks Groq API usage:
- Check `token_usage.json` for detailed stats
- Run `python -c "from token_tracker import get_usage_summary; print(get_usage_summary())"` for quick summary

---

## Project Files

| File | Purpose |
|------|---------|
| `auto_watcher.py` | Main auto-watcher script |
| `token_tracker.py` | Token usage tracking |
| `test_notion.py` | Notion connection test |
| `docs - Cam/Data Dump.md` | Original design specifications |
| `1-UPDATE - DO_NOT_CHANGE.md` | Update instructions |
| `2-WHERE AM I UPTO.md` | Current project status |
| `11-CHANGE LOG.md` | History of changes |