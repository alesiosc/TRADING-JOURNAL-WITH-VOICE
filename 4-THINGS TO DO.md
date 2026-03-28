# Things To Do

## Last Updated: 2026-03-28 19:50:00

## Priority Tasks

### High Priority
1. [x] Implement Auto-Watcher system (auto_watcher.py)
2. [x] Integrate Groq API for transcript parsing
3. [x] Integrate Notion API for automatic entries
4. [x] Implement token tracking system
5. [ ] Test end-to-end Auto-Watcher flow
6. [ ] Run auto_watcher.py and verify functionality

### Medium Priority
7. [ ] Set up keyboard shortcut integration (Right Ctrl → Notepad)
8. [ ] Configure hotkey_listener.py
9. [ ] Add screenshot capture capability
10. [ ] Test Zavi agent mode vs determine fallback to dictation mode
11. [ ] Create automation buttons in Notion
12. [ ] Test end-to-end voice-to-Notion workflow
13. [ ] Create Weekly Review template in Notion

### Low Priority
14. [ ] Explore AI pattern detection (future phase)
15. [ ] Consider mobile app integration
16. [ ] Add screenshot placeholders to Notion template

---

## Completed This Session

- Created auto_watcher.py with watchdog file monitoring
- Integrated Groq API (Llama 3.3 70B) for voice transcript parsing
- Integrated Notion API for automatic database entries
- Created token_tracker.py for usage monitoring
- Created test_notion.py for connection testing
- Implemented Voice-to-Structure Dictionary in auto_watcher.py
- Added archive system for processed files

---

## Known Issues

- Zavi agent mode showed UI instability in testing (2026-03-27)
- May need to implement Option 2 (dictation + glue layer) if agent mode fails
- Discipline Score formula may need real-world testing

---

## Ideas for Future Features

- Passive Listener mode for ambient emotional capture
- Multi-Layer Emotion Stack (dropdown + voice + inference)
- AI-Built Personal Vocabulary that evolves with usage
- The 90-Second Rule for post-loss reflection prompts

---

## Next Session Focus

1. Test the auto-watcher by creating a sample .txt file in trading_notes folder
2. Verify Notion entries are created automatically
3. Set up global keyboard shortcut for quick voice note capture