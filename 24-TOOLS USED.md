# Tools Used

## Last Updated: 2026-03-28 19:50:00

---

## Current Project Tools & Libraries

### Core Technologies

| Tool | Version | Purpose |
|------|---------|---------|
| **Zavi** | Latest (zavivoice.com) | Voice assistant for hands-free data entry |
| **Notion** | Cloud (notion.so) | Database for trading journal entries |
| **Claude 4.5** | Latest | AI assistant for brainstorming and development |
| **Groq API** | Latest | AI processing for voice transcript parsing |
| **Python** | 3.x | Scripting and automation |

### Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **watchdog** | Latest | File system monitoring for auto-watcher |
| **groq** | Latest | Groq API client for AI processing |
| **notion-client** | Latest | Notion API client |

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

### 3-Layer Architecture (Updated)
```
YOUR VOICE / TEXT FILE
    ↓
[Layer 1] WATCHDOG → monitors trading_notes folder
    ↓
[Layer 2] GROQ API (Llama 3.3 70B) → parses transcript, extracts structured data
    ↓
[Layer 3] NOTION API → receives structured data, writes to correct cells
```

### Auto-Watcher Workflow
1. User creates .txt file in ./trading_notes folder
2. Watchdog detects new file
3. Groq API parses transcript using Voice-to-Structure Dictionary
4. Notion API creates new page entry with extracted properties
5. File is archived to ./trading_notes/processed/

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

## API Keys & Configuration

### Groq API
- Key: YOUR_GROQ_API_KEY_HERE
- Model: llama-3.3-70b-versatile

### Notion API
- Token: ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f
- Database ID: 33109f62-78d4-80f6-9da5-dad7b6591885

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