# Fix .env file (overwrite old one)

# IMPORTANT: Add your actual API keys to .env manually
# DO NOT commit actual keys to version control
env_content = """# Trading Journal API Keys
# Add your keys here - DO NOT commit actual keys to version control
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
NOTION_TOKEN=YOUR_NOTION_TOKEN_HERE
DATABASE_ID=33109f62-78d4-80f6-9da5-dad7b6591885
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print(".env file updated with placeholder API keys")
print("\nIMPORTANT: Add your actual API keys to .env manually")
print("Make sure to add .env to .gitignore if using git!")
