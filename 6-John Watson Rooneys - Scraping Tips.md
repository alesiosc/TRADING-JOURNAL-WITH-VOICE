## here is a step-by-step breakdown of how the final data was obtained:

1. Website and API Inspection
   Opened Developer Tools: The first step was to open the Chrome Developer Tools and navigate to the "Network" tab to monitor web traffic.
   Filtered for API Requests: The requests were filtered by "Fetch/XHR" to isolate the backend API calls that return data in JSON format, which populates the website's front end.
   Identified Key Endpoints: By interacting with the website (scrolling, clicking on products, and searching), several key API endpoints were discovered:
   An endpoint for product data.
   An endpoint for product availability, including stock numbers.
   A search endpoint that returns a list of products based on a query.
2. Understanding and Manipulating the API
   Analyzed API URLs: The URLs of the identified API endpoints were copied and examined. It was found that they could be directly accessed and modified, for instance, by changing the product ID in the URL to get data for a different product.
   Tested Search Pagination: The search API's response was analyzed to understand its structure, including the total count of items and the number of items per page. By observing the network requests when navigating to the next page of search results, it was determined that the start parameter in the URL could be changed to paginate through the results.
3. Overcoming Blocking Mechanisms
   Initial Failures with curl and requests: Initial attempts to access the API endpoints using curl and the Python requests library failed, resulting in a "denied" message and a 403 error code, respectively. This happened even after adding a user-agent header.
   Identifying TLS Fingerprinting: The cause of the block was identified as TLS fingerprinting, a technique used by websites to detect and block automated requests.
   Using curl_cffi: To bypass this, the curl_cffi library was used in Python. By using the impersonate parameter set to "Chrome", the library mimics a real browser's TLS fingerprint, which led to a successful API request and a 200 status code.
4. Structuring and Running the Code
   Setting up the Environment: A Python virtual environment was created, and the necessary libraries (curl_cffi, rich, and pydantic) were installed.
   Data Modeling: pydantic models were created to define the structure of the expected data from the search and product detail APIs. This makes the data easier to work with.
   Creating API Functions:
   A function was written to create and configure a scraping session using curl_cffi, including settings for proxies.
   A function was developed to query the search API, handling the request and parsing the JSON response into the predefined pydantic models.
   Another function was created to fetch the detailed product information using the product ID obtained from the search results.
   Executing the Scrape:
   The main part of the script initialized a session.
   It then called the search function with a specific query (e.g., "hoodie").
   Finally, it looped through the search results and printed the name of each product, demonstrating the ability to successfully retrieve the desired data.

Here are the key points from the video and related modern Python web scraping insights for 2025:

1. Traditional tools like requests and BeautifulSoup remain useful but often fail against modern anti-bot defenses on websites.
2. Modern scraping requires asynchronous programming (async/await) and advanced libraries that support concurrency and proxy integration.
3. Creating persistent sessions/clients is critical for managing cookies and connection reuse effectively.
4. Using proxy rotation (e.g., Slice proxies) is essential to avoid IP bans and rate limits.
5. TLS fingerprint impersonation (e.g., via libraries like Arnet) helps bypass sophisticated blocking such as those used by Cloudflare.
6. LD+JSON embedded in web pages is a great place to extract structured product or listing data directly.
7. JSON parsing and selective scraping reduce the need for brittle XPath/CSS selectors by leveraging structured data.
8. Rate limiting with async semaphore controls scraping speed to avoid triggering blocks.
9. Modern scrapers combine headless browser impersonation with lightweight HTTP clients for efficiency and stealth.
10. Using helper libraries like select for parsing extracted HTML or JSON fragments simplifies the code.
11. Moving away from purely synchronous scraping workflows to fully async runs leads to better speed and resource usage.
12. Learning to use browser automation tools (Playwright, Puppeteer) can help scrape JavaScript-rendered content effectively.
13. Managing errors and retries gracefully is important for scale scraping projects.
14. Advanced techniques also include AI-assisted extraction, dynamic interaction simulation, and continuous adaptation to anti-bot changes.
15. Ethical considerations and legality should always be accounted for when scraping web data.

These points represent a modern, robust approach to Python web scraping that is effective in 2025's evolving web environment.

- Scraping Tips from John
  use Developer Console - Network Tab - API - json
  fingerprinting
  swapping requests for cur cffi and rnet (to send real looking browser fingerprinting)
  browsers timezone needs to be in sync with proxies timezones (if using them)
  http - rnet
  israelien rust
  camoufox
  hrequests
  scrapling
  pipelines
  scrapy

https://github.com/0x676e67/rnet

- SYNTHESIZED - Mistral
  Here is the **final synthesis** of the video, combining the transcript, code, and screenshots into a clear, step-by-step guide:

  ***

  ## **How to Scrape E-Commerce Sites: A Step-by-Step Guide**

  ### **1. Objective**
  - **Goal**: Scrape product data (name, price, availability, etc.) from e-commerce sites like Adidas.
  - **Approach**: Use the site's backend API instead of parsing HTML.

  ***

  ## **2. Finding the API Endpoints**

  ### **A. Inspect Network Traffic**
  - Open Chrome DevTools (`F12` or `Ctrl+Shift+I`).
  - Go to the **Network** tab, filter by **Fetch/XHR**, and look for **JSON responses**.
  - Interact with the site (search, click products) to find relevant API calls.

  ### **B. Key Endpoints Found**
  - **Search API**: `https://www.adidas.co.uk/api/plp/content-engine/search?query={query}&start={startIndex}`
  - **Product Detail API**: `https://www.adidas.co.uk/api/products/{productId}`
  - **Availability API**: `https://www.adidas.co.uk/api/products/{productId}/availability`

  ***

  ## **3. Understanding the API**
  - **Search API**: Returns a list of products matching a query, with pagination support.
  - **Product Detail API**: Returns detailed info (name, price, description, etc.) for a specific product.
  - **Availability API**: Returns stock levels and SKU details.

  ***

  ## **4. Writing the Scraper**

  ### **A. Setup**

  ```bash
   Copy
  pip install curl_cffi rich pydantic

  ```

  - Use `curl_cffi` to mimic a browser and avoid TLS fingerprinting issues.
  - Use `pydantic` for data modeling and validation.
  - Use `rich` for pretty printing.

  ### **B. Data Models**

  ```python
   Copy
  from pydantic import BaseModel
  from typing import Optional, List, Dict

  class SearchItem(BaseModel):
      productId: str
      modelId: str
      price: float
      salePrice: Optional[float]
      displayName: str
      rating: Optional[float]

  class SearchResponse(BaseModel):
      count: int
      startIndex: int
      searchTerm: str
      items: List[SearchItem]

  class ItemDetail(BaseModel):
      id: str
      name: str
      product_description: Dict
      pricing_information: Dict

  ```

  ### **C. API Interaction Functions**

  ```python
   Copy
  import os
  from curl_cffi import requests

  def new_session():
      session = requests.Session(impersonate="chrome")
      return session

  def search_api(session, query: str, start_num: int):
      url = f"https://www.adidas.co.uk/api/plp/content-engine/search?query={query}&start={start_num}"
      resp = session.get(url)
      resp.raise_for_status()
      search = SearchResponse(**resp.json()["raw"]["itemList"])
      return search

  def detail_api(session, item: SearchItem):
      url = f"https://www.adidas.co.uk/api/products/{item.productId}"
      resp = session.get(url)
      resp.raise_for_status()
      product = ItemDetail(**resp.json())
      return product

  ```

  ### **D. Main Function**

  ```python
   Copy
  def main():
      session = new_session()
      search = search_api(session, "hoody", 1)
      for item in search.items:
          product = detail_api(session, item)
          print(f"Product: {product.name}, Price: {product.pricing_information['currentPrice']}")

  if __name__ == "__main__":
      main()

  ```

  ***

  ## **5. Debugging and Proxies**
  - **403 Errors**: Use `curl_cffi` with `impersonate="chrome"` to avoid TLS fingerprinting issues.
  - **Proxies**: Use high-quality residential or mobile proxies (e.g., ProxyScrape) to avoid IP blocking.
  - **Sticky Sessions**: Hold onto a single IP for a few minutes to mimic human behavior.

  ***

  ## **6. Example Output**

  When you run the script, it prints product names and prices:

  ```
   Copy
  Product: Essentials Fleece Hoodie, Price: £45.00
  Product: Adicolor Hoodie, Price: £55.00
  Product: Trefoil Essentials Hoodie, Price: £50.00
  ...

  ```

  ***

  ## **7. Key Takeaways**
  - **APIs are easier**: Scraping APIs is more reliable than parsing HTML.
  - **Mimic browsers**: Use `curl_cffi` and proper headers to avoid blocks.
  - **Respect the site**: Don’t hammer the API; use proxies and rate limiting.
  - **Data modeling**: Use Pydantic to keep your data clean and validated.

  ***

  ## **8. Final Notes**
  - This method works for most e-commerce sites.
  - Always check the site’s `robots.txt` and terms of service.
  - For more details, watch the full video and check the related resources.
