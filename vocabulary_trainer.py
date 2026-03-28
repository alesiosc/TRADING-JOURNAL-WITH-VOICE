import json
import os

VOCAB_FILE = "vocabulary_training.json"

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
    if category in vocab and value in vocab[category]:
        if phrase.lower() not in vocab[category][value]:
            vocab[category][value].append(phrase.lower())
            save_vocab(vocab)
            return True
    return False

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

# Initialize vocabulary file
if not os.path.exists(VOCAB_FILE):
    save_vocab(DEFAULT_VOCAB)
    print("Vocabulary training file created!")
else:
    print("Vocabulary training file loaded.")
