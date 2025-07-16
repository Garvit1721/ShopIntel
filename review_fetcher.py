# --- review_fetcher.py ---
import requests
import time
from bs4 import BeautifulSoup
from logger_context import call_id_var
from logger_util import setup_logger

logger = setup_logger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/114.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.5'
}

MAX_RETRIES = 5
RETRY_DELAY = 4  # seconds

class ReviewFetcher:
    """
    Fetches customer reviews from a specific Flipkart product review page URL.
    """

    def __init__(self):
        pass

    def get_html_soup(self, url: str):
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=HEADERS)
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 429:
                    logger.warning(f"[{call_id_var.get()}] Rate limited (429). Retrying in {RETRY_DELAY}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"[{call_id_var.get()}] Failed to fetch page. Status: {response.status_code}")
                    return None
            except Exception as e:
                logger.exception(f"[{call_id_var.get()}] Exception while fetching HTML (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
        logger.error(f"[{call_id_var.get()}] Max retries reached. Failed to fetch page.")
        return None

    def extract_reviews_from_page(self, soup):
        reviews = []
        rows = soup.find_all('div', class_=['col', 'EPCmJX'])

        for row in rows:
            try:
                sub_row = row.find_all('div', class_='row')
                if len(sub_row) < 4:
                    continue

                rating = sub_row[0].find('div').get_text(strip=True)
                summary = sub_row[0].find('p').get_text(strip=True)
                review = sub_row[1].find_all('div')[2].get_text(strip=True)

                location_tag = sub_row[3].find('p', class_='_2mcZGG')
                location = "Unknown"
                if location_tag:
                    span_tags = location_tag.find_all('span')
                    if len(span_tags) > 1:
                        location = "".join(span_tags[1].get_text().split(",")[1:]).strip()

                date_tags = sub_row[3].find_all('p', class_='_2sc7ZR')
                date = date_tags[1].get_text(strip=True) if len(date_tags) > 1 else "Unknown"

                sub_row_2 = row.find_all('div', class_='_1e9_Zu')
                upvotes, downvotes = "0", "0"
                if sub_row_2:
                    spans = sub_row_2[0].find_all('span', class_='_3c3Px5')
                    if len(spans) >= 2:
                        upvotes = spans[0].get_text(strip=True)
                        downvotes = spans[1].get_text(strip=True)

                reviews.append({
                    "rating": rating,
                    "summary": summary,
                    "review": review,
                    "location": location,
                    "date": date,
                    "upvotes": upvotes,
                    "downvotes": downvotes
                })

            except Exception as e:
                logger.warning(f"[{call_id_var.get()}] Error parsing a review block: {e}")

        return reviews

    def get_reviews_from_url(self, url: str) -> list:
        soup = self.get_html_soup(url)
        if not soup:
            logger.error(f"[{call_id_var.get()}] Failed to fetch or parse HTML.")
            return []
        return self.extract_reviews_from_page(soup)


if __name__ == "__main__":
    url = "https://www.flipkart.com/boat-storm-call-w-4-29-cm-1-69-bt-calling-550-nits-brightness-smartwatch/product-reviews/itmc36011d1d910a?pid=SMWGNFSFHYHP4UAU"

    fetcher = ReviewFetcher()
    reviews = fetcher.get_reviews_from_url(url)

    print(f"Total reviews fetched: {len(reviews)}")
    print(reviews)