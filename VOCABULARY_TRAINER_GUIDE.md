# Vocabulary Trainer - Auto-Sync Guide

## Overview
The Vocabulary Trainer now automatically syncs with your Notion database columns and their values.

## How It Works

### Automatic Column Detection
- Fetches all select and multi_select columns from Notion database
- Displays columns with their actual Notion names
- Values pulled directly from Notion options

### Excluded Columns
- Name, Date, AI_Analysis, Transcript, Screenshots

### Syncing Process
1. On Launch: Calls sync_vocab_with_notion() to fetch latest columns
2. New Columns: Automatically added with empty phrase lists
3. New Options: Automatically detected when added to Notion
4. Preserved Data: Trained phrases never deleted

## Current Detected Columns
- 5m Form: Perfect, Well-Formed, Decent, Questionable, Poor
- Emotions: Zen, Anxious, FOMO, Revenge
- M5_Pattern: Hammer, Shooting Star, Bullish Engulfing, Bearish Engulfing
- Entry_Direction: Buy, Sell
- M1_Confirm: Yes, No
- Level_Types: LIS, 2D AVWAP, Lower, Upper, Mid, Set 1, Set 2, BK Brown, Extremes

## Usage
1. Run python vocabulary_trainer_ui.py
2. UI syncs with Notion automatically
3. Review unknown phrases
4. Select column and value
5. Save or Skip
6. Click Finish when done