WARNING - MESSAGE TO CLI. i tell you not to touch the text in here. DO NOT delete this imporatnat information. thsi is the impoartant information i dont want you to touch. - WARNING

Here's a step-by-step guide for scraping trainer shops like Nike, ASOS, Adidas, etc., using Scrapling as your foundation. This includes fallback strategies for challenges like anti-bot systems, dynamic content, or changing site structures.

Step 1: Choose Your Tooling
Scrapling provides 3 core fetchers for different scenarios:

Static Sites (no JavaScript rendering):
Use Fetcher for sites like Nike or Adidas (if pages are static).
Dynamic Sites (JavaScript-heavy):
Use DynamicFetcher (e.g., ASOS or sites with infinite scroll).
Anti-Bot Protected Sites (Cloudflare, CAPTCHA):
Use StealthyFetcher (e.g., sites with anti-scraping measures).
Install Scrapling:

pip install scrapling[scraping] # Basic scraping
pip install scrapling[shell] # For CLI/Interactive Shell
pip install scrapling[ai] # If using MCP Server (advanced)
Step 2: Setup & Configuration
Install Playwright Browsers (required for DynamicFetcher/StealthyFetcher):
scrapling install # Downloads browsers (Chromium, Firefox, etc.)
Import Required Classes:
from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher
from scrapling.parser import Selector
Step 3: Plan Your Scraping Workflow
Define Targets:

Example: Product titles, prices, availability on Nike.com.
Example URLs:
https://www.nike.com/running-shoes/
https://www.asos.com/men/footwear/running-shoes/
Check robots.txt:

Example: https://www.nike.com/robots.txt
Respect crawl delays and disallowed paths.
Step 4: Write a Basic Scraper (Static Site)
from scrapling.fetchers import Fetcher
from scrapling.parser import Selector

# Step 4.1: Fetch Page Content

page = Fetcher.get("https://www.nike.com/running-shoes/")

# Step 4.2: Create Selector Object

selector = Selector(page.source, url=page.parsed_url)

# Step 4.3: Extract Data (CSS Selectors)

product_blocks = selector.css("div.product-card")
for product in product_blocks:
title = product.css("h3.product-title", first=True).text.strip()
price = product.css("span.product-price", first=True).text.strip()
print(f"{title} - {price}")
Fallback Options for Dynamic/Anti-Bot Sites
Option 1: Dynamic Content (JavaScript-Rendered Sites)

# Use DynamicFetcher for sites like ASOS

page = DynamicFetcher.fetch(
"https://www.asos.com/men/footwear/running-shoes/",
network_idle=True # Wait for JS to render
)

# Parse with Selector as before

selector = Selector(page.source)
...
Option 2: Anti-Bot Sites (Cloudflare, CAPTCHA)

# Use StealthyFetcher for sites with anti-bot systems

page = StealthyFetcher.fetch(
"https://www.schu.co.uk/running-shoes",
solve_cloudflare=True # Auto-solves simple Cloudflare challenges
)
Step 5: Robust Parsing with Adapters
Adaptive Parsing for Evolving Sites
Use Selector to handle changing DOM structures:

# First scrape and save element structure

element = selector.css("#product-title", auto_save=True)

# Later, retrieve it even if the DOM changes

adaptive_element = selector.css("#product-title", adaptive=True)
Step 6: Save/Export Data
Options: CSV/JSON/Databases. Example using CSV:

import csv

data = [
{"title": "Nike Air Max", "price": "£150"},
{"title": "Adidas Ultraboost", "price": "£200"},
]

with open("shoes.csv", "w") as f:
writer = csv.DictWriter(f, fieldnames=["title", "price"])
writer.writeheader()
writer.writerows(data)
Step 7: Fallback Strategies
Rate Limiting:
from time import sleep
sleep(5) # Wait 5s between requests to avoid bans
Proxy Rotation: Use StealthyFetcher with:
page = StealthyFetcher.fetch(url, proxy="http://user:pass@proxy:port")
Adaptive Selectors: Use generate_css_selector() to dynamically extract paths.
Step 8: Advanced Tools
Interactive Shell: Test selectors in real-time:
scrapling shell

> > > get("https://www.asos.com/running-shoes/")
> > > page.css("div.product")
> > > MCP Server for AI Integration: Deploy an AI-powered scraper:
> > > from scrapling.core.ai import ScraplingMCPServer
> > > server = ScraplingMCPServer()
> > > server.serve() # Exposes methods via MCP protocol
> > > Step 9: Automate & Schedule
> > > Use cron (Linux) or Task Scheduler (Windows) for daily scrapes:

# Example cronjob (runs daily at 2AM)

0 2 \* \* \* /usr/bin/python3 /path/to/scraper.py
Step 10: Debugging & Error Handling
Logging:
from scrapling.core.utils import configure_logger
configure_logger(level="DEBUG")
Fallback Selectors: Use XPath or multiple CSS selectors:
selector.css("[itemprop='name']") or selector.xpath("//h1[@class='product']")
Legal/Ethical Notes
Add throttling to avoid server overload.
Use StealthyFetcher to mimic browser behavior and reduce bans.
This workflow gives you a solid foundation with multiple fallback options for challenges like anti-bot systems, JS rendering, or site redesigns. Adapt the tooling (Fetcher class) based on the target site's complexity.

Implementation Notes from BMAD Sanchia AIO Scraper Project:

After implementing Scrapling in the BMAD Sanchia AIO Scraper project, we learned several important lessons:

Key Implementation Challenges:

1. API Parameter Configuration: Difficulty identifying correct parser keywords - the valid ones are ('huge_tree', 'adaptive', 'storage', 'keep_cdata', 'storage_args', 'keep_comments', 'adaptive_domain')
2. Method Signatures: Confusion between different configuration approaches
3. Documentation Gaps: Need for more comprehensive usage examples
4. Compatibility Issues: Integration challenges with existing codebase

Scrapling's Advanced Features Successfully Implemented:

1. Browser Fingerprint Spoofing: Essential for evading modern bot detection systems
2. TLS Fingerprint Impersonation: Important for avoiding network-level detection
3. Cloudflare Turnstile Bypass Capabilities: Automatically handles Cloudflare challenges
4. Custom Stealth Mode: Browser automation that avoids common detection vectors
5. Header Spoofing: Realistic HTTP headers to mimic genuine browser requests
6. Session Management: Cookie and state management for continuous scraping
7. Adaptive Scraping: Smart element tracking that relocates elements after website changes
8. Async Support: Complete async support across all fetchers with dedicated async session classes, enabling concurrent scraping operations

Fetcher Classes Usage:

- Fetcher: Fast HTTP requests with browser impersonation (TLS fingerprint, headers, HTTP3 support)
- StealthyFetcher: Advanced stealth capabilities using a modified Firefox version with fingerprint spoofing that can bypass Cloudflare Turnstile
- DynamicFetcher: Full browser automation supporting Playwright's Chromium, real Chrome, and custom stealth mode

Key Anti-Bot Features:

- Browser fingerprint spoofing
- TLS fingerprint impersonation
- Cloudflare Turnstile bypass capabilities
- Custom stealth mode for browser automation
- Header spoofing and browser impersonation

Session Management:

- Persistent sessions with cookie and state management
- FetcherSession, StealthySession, and DynamicSession classes
- Automatic session lifecycle handling with proper cleanup
- Support for concurrent isolated sessions

Adaptive Scraping:

- Smart element tracking that relocates elements after website changes
- Intelligent similarity algorithms for element relocation
- Automatic finding of similar elements
- Robust selector generation that survives website design changes

HTTP-based Fetchers:

1. Fetcher: Basic HTTP requests with optional browser impersonation
2. StealthyFetcher: Enhanced stealth mode with fingerprint spoofing

Browser-based Fetchers:

1. DynamicFetcher: Full browser automation with stealth capabilities
2. StealthyFetcher: Modified Firefox with advanced fingerprinting bypass

Session Variants:
Each fetcher has session equivalents:

- FetcherSession, AsyncFetcherSession
- StealthySession, AsyncStealthySession
- DynamicSession, AsyncDynamicSession

Async Support:
Complete async support across all fetchers with dedicated async session classes, enabling concurrent scraping operations.

Lessons Learned from Scrapling Implementation:

1. Parameter Configuration: Use valid parser keywords from `parser_keywords` property
2. Configuration Before Fetching: Apply settings before making requests
3. Error Handling: Implement proper exception handling for anti-bot challenges
4. Debugging: Save response content for analysis of anti-bot measures
5. API Documentation: Create comprehensive usage examples for each fetcher type
6. Error Handling: Implement more robust anti-bot challenge detection
7. Configuration Validation: Add better parameter validation and error messages
8. Debugging Tools: Enhance debugging capabilities for anti-bot analysis

Best Practices Discovered:

1. Correct Parameter Usage: Use valid parser keywords from `parser_keywords` property
2. Configuration Before Fetching: Apply settings before making requests
3. Error Handling: Implement proper exception handling for anti-bot challenges
4. Debugging: Save response content for analysis of anti-bot measures
5. API Documentation: Create comprehensive usage examples for each fetcher type
6. Error Handling: Implement more robust anti-bot challenge detection
7. Configuration Validation: Add better parameter validation and error messages
8. Debugging Tools: Enhance debugging capabilities for anti-bot analysis
