# Things To Do

## Last Updated: 2026-03-29 18:21:00

---

## 🔴 High Priority (This Week)

### 1. Add Actual API Keys to .env
**Why**: The system is ready but has placeholder keys
**Action**: 
- Get your Groq API key from console.groq.com
- Get your Notion integration token from notion.so/my-integrations
- Add both to the `.env` file

**Status**: ⏳ Waiting for user action

---

### 2. Test End-to-End Flow
**Why**: Verify everything works together
**Action**: 
1. Start auto_watcher.py
2. Create a test text file in trading_notes/
3. Check Notion for new entry
4. Verify properties were extracted correctly

**Status**: ⏳ Waiting for API keys

---

## 🟡 Medium Priority (Next Week)

### 3. Set Up Keyboard Shortcut
**Why**: Faster voice capture workflow
**Action**: Configure Right Ctrl + N to open Notepad quickly

**Status**: 🔜 Not started

---

### 4. Refine Voice-to-Structure Dictionary
**Why**: Improve parsing accuracy based on real usage
**Action**: 
- Test with various voice transcript formats
- Add new patterns as needed
- Document successful patterns

**Status**: 🔜 Not started

---

### 5. Add Screenshot Integration
**Why**: Capture visual context of trades
**Action**: 
- Modify auto_watcher to detect screenshot references
- Add screenshot URLs to Notion entries
- Create a screenshot naming convention

**Status**: 🔜 Not started

---

## 🟢 Low Priority (Future)

### 6. Create Usage Dashboard
**Why**: Visual overview of trading patterns
**Action**: 
- Build a simple HTML dashboard
- Pull data from Notion API
- Show trading stats and trends

**Status**: 📋 Backlog

---

### 7. Add Multiple Database Support
**Why**: Separate databases for different strategies
**Action**: 
- Create config for multiple database IDs
- Add routing logic based on file prefix
- Allow switching databases via .env

**Status**: 📋 Backlog

---

### 8. Mobile Integration
**Why**: Capture trades from phone
**Action**: 
- Set up IFTTT or Zapier for mobile text → folder sync
- Create a mobile-friendly capture method

**Status**: 📋 Backlog

---

### 9. Voice Command Shortcuts
**Why**: Even faster entry
**Action**: 
- Add hotword detection (e.g., "journal this")
- Create quick command patterns
- Integrate with Zavi voice assistant

**Status**: 📋 Backlog

---

### 10. Backup & Sync
**Why**: Prevent data loss
**Action**: 
- Set up automatic Notion export
- Create local backup schedule
- Add cloud sync for trading_notes folder

**Status**: 📋 Backlog

---

## ✅ Completed Items

| Task | Completed |
|------|-----------|
| Set up project structure | ✅ 2026-03-27 |
| Create auto_watcher.py | ✅ 2026-03-28 |
| Implement Groq API integration | ✅ 2026-03-28 |
| Add Notion API integration | ✅ 2026-03-28 |
| Create voice-to-structure dictionary | ✅ 2026-03-28 |
| Add token tracking | ✅ 2026-03-28 |
| Set up environment variables | ✅ 2026-03-29 |
| Push to GitHub | ✅ 2026-03-29 |
| Remove hardcoded secrets | ✅ 2026-03-29 |
| Document system | ✅ 2026-03-29 |

---

## 📋 Project Maintenance

### Weekly Tasks
- Check token usage in token_usage.json
- Review processed folder for any issues
- Update 1-UPDATE.md with progress

### Monthly Tasks
- Review and archive old entries
- Check GitHub for any issues
- Backup Notion database

---

## 🚀 Quick Wins

1. **Add one test entry** - Just create a simple text file and run the watcher
2. **Set up keyboard shortcut** - 5-minute setup, instant productivity boost
3. **Share feedback** - Tell me what works and what doesn't

---

## 📞 Support

For issues or questions:
- Check `3-HOW TO RUN.md` for troubleshooting
- Check `2-WHERE AM I UPTO.md` for current status
- Check `11-CHANGE LOG.md` for recent changes
- Check `24-TOOLS USED.md` for tool documentation