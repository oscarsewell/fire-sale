# Full Scraping Module

The partial scraping module extracts volatile product data from our top retailers. This is triggered periodically on a high-frequency basis. It is used to keep the current price of products in our database up to date without wasting resources on retrieving static metadata (such as product name, original price, and currency).

---

## Project Structure

### Directories
`awd_it`, `ebuyer` and `overclockers`: Directories for each supported website.

### Files
- `requirements.txt`: Contains external libraries (beautifulsoup4, curl-cffi, pytest, pylint) required to run, test, and lint the scraper scripts.

Each website directory contains:
- `[WEBSITE-NAME]_scraper.py`: Fully scrapes the product data for a given URL.
- `conftest.py`: Houses reusable test fixtures, mock server configurations, and mock HTML responses representing active or deleted listings.
- `test_[WEBSITE-NAME]_scraper.py`: Automated unit tests verifying extraction accuracy, parser boundary behaviors, and custom exception handling under mock network requests.

---

## How to Run the Files

Each scraper can be executed manually from the terminal. Running a scraper script directly triggers its demo block, which fetches and prints a product information dictionary for a real sample product.

To run a scraper, execute the script from the root workspace directory:

```bash
# AWD-IT
python3 partial_scraping/awd-it/awd_it_scraper.py

# Ebuyer
python3 partial_scraping/ebuyer/ebuyer_scraper.py

# Overclockers
python3 partial_scraping/overclockers/overclockers_scraper.py
```

## How to Run the Tests

Automated testing is integrated using pytest.

1. Preparation
Ensure that all testing and scraping dependencies have been installed:

```bash
pip install -r partial_scraping/requirements.txt
```

2. Run All Tests
Execute all tests across the full scraping module in one go:

```bash
pytest partial_scraping/
```

3. Run Specific Retailer Tests
To target unit tests for a single scraper folder or file, run pytest against that specific directory or file path:

```bash
# E.g Run AWD-IT tests only
pytest partial_scraping/awd-it/
```

## Inputs and Outputs

A list of tuples, each containing a product URL and its database ID, is processed, and a consistent list of dictionaries is returned.

### Product dictionary structure
Upon a successful extraction, the scraper yields the following structure for each dictionary:

```json
{
  "product_id": 1,
  "url": "https://www.example.com/product-page.html",
  "current_price": "£104.99",
  "currency_code": "GBP",
  "page_exists": true,
  "scraped_at": "2026-06-05T14:32:00.123456"
}
```
