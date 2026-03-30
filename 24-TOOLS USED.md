# Tools Used

## Last Updated: 2026-03-30 12:53:00

---

## Current Project Tools & Libraries

### Core Technologies

| Tool | Version | Purpose |
|------|---------|---------|
| **Groq API** | Latest | AI processing for voice transcript parsing (Llama 3.3 70B) |
| **Notion** | Cloud (notion.so) | Database for trading journal entries |
| **Zavi** | Latest (zavivoice.com) | Optional voice assistant for hands-free data entry |
| **Python** | 3.x | Scripting and automation |
| **Git** | Latest | Version control |
| **GitHub** | Cloud | Remote repository hosting |

### Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **watchdog** | Latest | File system monitoring for auto-watcher |
| **groq** | Latest | Groq API client for AI processing |
| **notion-client** | Latest | Notion API client |
| **python-dotenv** | Latest | Environment variable management |

### Development Tools

| Tool | Purpose |
|------|---------|
| **VS Code** | Code editor |
| **Git** | Version control |
| **PowerShell** | Command line (Windows) |

---

## Project-Specific Implementations

### Voice-to-Structure Dictionary
Custom mapping system connecting natural language to Notion database fields:
- "hammer" → M5_Anchor: "Hammer"
- "shooting star" → M5_Anchor: "Shooting Star"
- "blue level" → Level_Type: "Ludwig Blue"
- "red level" → Level_Type: "Ludwig Red"
- "LIS" → Level_Type: "LIS"
- "BKBrown" → Level_Type: "BKBrown"
- "calm", "zen" → Internal_State: "Zen"
- "anxious", "nervous" → Internal_State: "Anxious"
- "FOMO" → Internal_State: "FOMO"
- "revenge", "tilted" → Internal_State: "Revenge"
- "chased" → Patience_Grade: "F"
- "waited", "patient" → Patience_Grade: "A"
- "impulse [number]" → Impulse: [number]
- "confirmed" → M1_Confirm: true

### Auto-Watcher Architecture
```
TEXT FILE IN trading_notes/
    ↓
[Watchdog] monitors folder for new .txt files
    ↓
[Groq API] parses transcript using Voice-to-Structure Dictionary
    ↓
[Notion API] creates new page entry with extracted properties
    ↓
[Archive] moves processed file to ./trading_notes/processed/
```

### Token Tracking System
- Tracks Groq API usage (prompt tokens, completion tokens)
- Stores daily, monthly, and all-time totals in token_usage.json
- Provides get_usage_summary() function for quick status checks

### Discipline Score Formula
```javascript
let(setupScore, if(prop("M1 Confirm"), 50, 0),
let(levelScore, if(empty(prop("Level Type")), 0, 30),
let(mindsetBonus, if(prop("Internal State") == "Zen", 20, if(prop("Internal State") == "Anxious", -10, 0)),
setupScore + levelScore + mindsetBonus)))
```

---

## Security Configuration

### Environment Variables (.env)
API keys are stored in a local `.env` file (not committed to version control):
- `GROQ_API_KEY` - Groq API key
- `NOTION_TOKEN` - Notion integration token
- `DATABASE_ID` - Notion database ID (33109f62-78d4-80f6-9da5-dad7b6591885)

### GitHub Repository
- Repository: https://github.com/alesiosc/TRADING-JOURNAL-WITH-VOICE
- .env file is in .gitignore
- All API keys are placeholders in committed code

---

## Future Tools to Consider

- **Make.com** or **n8n** - For automation/glue layer (fallback option)
- **OpenAI API** - For AI parsing of voice transcripts (alternative to Groq)
- **Playwright** / **Cypress** - For test automation (future phases)

---

## Browser & Environment

- **Browser**: Chrome/Edge (for Notion and Zavi web interfaces)
- **OS**: Windows 10
- **Shell**: PowerShell 7
- **Python**: 3.x

---

## Session Update (2026-03-30)

### Files Updated This Session
- **11-CHANGE LOG.md** - Version 8 added with status file update entry
- **2-WHERE AM I UPTO.md** - Refreshed with current date and pending tasks
- **3-HOW TO RUN.md** - Added note about system readiness
- **20-LAST CONVO.md** - Updated session summary for next chat
- **24-TOOLS USED.md** - This file, appended with session update

### System Status
- All status files synchronized with timestamp 2026-03-30 12:53:00
- No code changes made - documentation refresh only
- Ready for use once API keys added to .env file

### Project State
- **Main branch**: Clean working directory
- **GitHub**: Pushed 2026-03-29, no pending changes
- **Configuration**: Placeholder API keys in place, awaiting user credentials