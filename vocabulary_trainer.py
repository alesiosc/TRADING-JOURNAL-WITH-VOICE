import json
import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

VOCAB_FILE = "vocabulary_training.json"
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

EXCLUDED_COLUMNS = ["Name", "Date", "AI_Analysis", "Transcript", "Screenshots", "Impulse", "Patience"]
INCLUDED_COLUMNS = ["Emotions", "M5_Pattern", "5m Form", "Level_Types", "M1_Confirm", "Entry_Direction"]

DEFAULT_VOCAB = {
    "well_formed_quality": {
        "Perfect": ["textbook", "perfect", "beautiful", "flawless"],
        "Well-Formed": ["clean", "good", "solid", "nice", "well formed"],
        "Decent": ["okay", "alright", "decent", "fine"],
        "Questionable": ["iffy", "questionable", "not great", "sketchy"],
        "Poor": ["messy", "ugly", "bad", "terrible", "poor"]
    },
    "emotions": {
        "Zen": ["calm", "zen", "relaxed", "chill", "peaceful"],
        "Anxious": ["nervous", "anxious", "worried", "stressed"],
        "FOMO": ["fomo", "fear of missing out", "rushing", "hasty"],
        "Revenge": ["revenge", "tilted", "angry", "frustrated", "mad"]
    },
    "m5_pattern": {
        "Hammer": ["hammer"],
        "Shooting Star": ["shooting star", "shooter"],
        "Bullish Engulfing": ["bullish engulfing", "bull engulf"],
        "Bearish Engulfing": ["bearish engulfing", "bear engulf"]
    },
    "entry_direction": {
        "Buy": ["buy", "bought", "long", "going long", "entered long"],
        "Sell": ["sell", "sold", "short", "going short", "entered short", "shorted"]
    },
    "m1_confirm": {
        "Yes": ["confirmed", "m1 confirmed", "yes", "got confirmation"],
        "No": ["no confirm", "didn't confirm", "no", "not confirmed"]
    },
    "unknown_phrases": []
}

def get_notion_columns():
    try:
        notion = Client(auth=NOTION_TOKEN)
        db = notion.databases.retrieve(database_id=DATABASE_ID)
        
        # Get all properties in Notion's order
        all_properties = list(db['properties'].items())
        
        # Filter and maintain order
        columns = {}
        for prop_name, prop_data in all_properties:
            prop_type = prop_data['type']
            
            # Only include columns in INCLUDED_COLUMNS list
            if prop_name not in INCLUDED_COLUMNS:
                continue
                
            if prop_type in ['select', 'multi_select']:
                options = prop_data.get(prop_type, {}).get('options', [])
                column_key = prop_name.lower().replace(' ', '_')
                columns[column_key] = {
                    'display_name': prop_name,
                    'type': prop_type,
                    'options': [opt['name'] for opt in options],
                    'order': INCLUDED_COLUMNS.index(prop_name)  # Store Notion order
                }
        
        # Sort by Notion order
        sorted_columns = dict(sorted(columns.items(), key=lambda x: x[1]['order']))
        return sorted_columns
    except Exception as e:
        print("Error fetching Notion columns: {}".format(e))
        return {}

def sync_vocab_with_notion():
    vocab = load_vocab()
    notion_columns = get_notion_columns()
    if not notion_columns:
        print("Warning: Could not fetch Notion columns. Using existing vocabulary.")
        return vocab
    for column_key, column_info in notion_columns.items():
        if column_key not in vocab or column_key == "unknown_phrases":
            vocab[column_key] = {}
            for option in column_info['options']:
                vocab[column_key][option] = []
        else:
            existing_options = set(vocab[column_key].keys())
            notion_options = set(column_info['options'])
            for option in notion_options - existing_options:
                vocab[column_key][option] = []
    if "unknown_phrases" not in vocab:
        vocab["unknown_phrases"] = []
    save_vocab(vocab)
    return vocab

def load_vocab():
    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_VOCAB.copy()

def save_vocab(vocab):
    with open(VOCAB_FILE, 'w') as f:
        json.dump(vocab, f, indent=2)

def add_phrase(category, value, phrase):
    vocab = load_vocab()
    
    # Ensure category exists
    if category not in vocab:
        print(f"Category '{category}' not found in vocab")
        return False
    
    # Ensure value exists in category
    if value not in vocab[category]:
        print(f"Value '{value}' not found in category '{category}'")
        print(f"Available values: {list(vocab[category].keys())}")
        return False
    
    # Ensure the value has a list (not dict or other type)
    if not isinstance(vocab[category][value], list):
        vocab[category][value] = []
    
    # Add phrase if not already present
    if phrase.lower() not in vocab[category][value]:
        vocab[category][value].append(phrase.lower())
        save_vocab(vocab)
        return True
    
    return True  # Already exists, still success

def find_match(text, category):
    vocab = load_vocab()
    text_lower = text.lower()
    if category not in vocab:
        return None
    for value, phrases in vocab[category].items():
        for phrase in phrases:
            if phrase in text_lower:
                return value
    return None

def get_all_categories():
    vocab = load_vocab()
    return list(vocab.keys())

def get_unknown_phrases():
    vocab = load_vocab()
    return vocab.get("unknown_phrases", [])

def add_unknown_phrase(phrase):
    vocab = load_vocab()
    if "unknown_phrases" not in vocab:
        vocab["unknown_phrases"] = []
    if phrase.lower() not in vocab["unknown_phrases"]:
        vocab["unknown_phrases"].append(phrase.lower())
        save_vocab(vocab)

def has_unknown_phrases():
    return len(get_unknown_phrases()) > 0

if not os.path.exists(VOCAB_FILE):
    save_vocab(DEFAULT_VOCAB)