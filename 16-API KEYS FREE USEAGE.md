Instructions for Use in Another Project

  1. Copy the Module:
  Place the free_ai_api_groq_openrouter_with_logging.py file into your project directory.

  2. Install Dependencies:
  In your project's terminal, install the required libraries from the updated requirements.txt (or manually):

   1 pip install -r requirements.txt
  Alternatively, you can install them manually:
   1 pip install requests python-dotenv

  3. Create the `.env` File:
  In the root directory of your new project, create a file named .env. The module will automatically find and use this file. Add the necessary API keys and credentials as shown
  below.

  *Note:* *Only the providers you provide keys for will be enabled.*

    1 # For Cloudflare
    2 CLOUDFLARE_API_KEY="your_cloudflare_api_key"
    3 CLOUDFLARE_ACCOUNT_ID="your_cloudflare_account_id"
    4 
    5 # For OpenRouter
    6 OPENROUTER_API_KEY="your_openrouter_api_key"
    7 
    8 # For Clarifai
    9 CLARIFAI_API_KEY="your_clarifai_api_key"
   10 
   11 # For Groq
   12 GROQ_API_KEY="your_groq_api_key"

  4. Use the Module in Your Code:
  You can now import and use the get_client function anywhere in your project. The client will be pre-configured with the providers you enabled in your .env file.

  Example Usage:

    1 from free_ai_api_groq_openrouter_with_logging import get_client
    2 
    3 # 1. Get the client instance. It's automatically configured from your .env file.
    4 client = get_client()
    5 
    6 # 2. Use the client to generate text.
    7 # It will automatically rotate between your enabled providers.
    8 try:
    9     prompt = "In 50 words, explain what makes a good programmer."
   10     response = client.generate_text(prompt)
   11     print("AI Response:", response)
   12 
   13     # 3. (Optional) You can also specify a preferred provider.
   14     # The client will use it if it's available and within its limits.
   15     print("\\n--- Trying a preferred provider ---")
   16     response_from_groq = client.generate_text(
   17         prompt,
   18         provider_preference="groq",
   19         # You can also pass provider-specific arguments
   20         model="llama3-8192"
   21     )
   22     print("Groq Response:", response_from_groq)
   23 
   24 
   25     # 4. (Optional) Check your usage statistics
   26     stats = client.get_usage_stats()
   27     print("\\n--- Usage Stats ---")
   28     print(stats)
   29 
   30 except Exception as e:
   31     print(f"An error occurred: {e}")

  This revised approach is more robust and makes the module much easier to drop into any project.