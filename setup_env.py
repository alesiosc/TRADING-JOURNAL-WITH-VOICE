# Move sensitive data to .env file

import os

# Create .env file with all API keys
env_content = """# Trading Journal API Keys
# Add your keys here - DO NOT commit actual keys to version control
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
NOTION_TOKEN=YOUR_NOTION_TOKEN_HERE
DATABASE_ID=33109f62-78d4-80f6-9da5-dad7b6591885
"""

with open('.env', 'w') as f:
    f.write(env_content)

print(".env file created with API keys")
print("\nNow updating trading_journal_final.py to use .env...")

# Update main file to load from .env
with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add python-dotenv import at top
if 'from dotenv import load_dotenv' not in content:
    content = content.replace('import os', 'import os\nfrom dotenv import load_dotenv')

# Replace hardcoded keys with env variables
old_config = '''# Configuration
# Load from environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")'''

new_config = '''# Configuration
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")'''

content = content.replace(old_config, new_config)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated trading_journal_final.py to load from .env")
print("\nInstalling python-dotenv...")
