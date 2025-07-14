# --- data_fetcher.py ---
import time
import os
import requests
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException
from logger_util import setup_logger


logger = setup_logger(__name__)
load_dotenv()


class DataFetcher:
    def __init__(self):
        self.url = None
        self.driver = None

    def fetch_product_info(self, url: str = None, driver: Optional[uc.Chrome] = None) -> Dict[str, Any]:
        # Use provided URL or fallback to instance URL
        if url:
            self.url = url
        if driver:
            self.driver = driver
            
        if not self.url:
            logger.error("No URL provided for product info fetch")
            return {"error": "No URL provided"}
            
        if not self.driver:
            logger.error("No driver provided for product info fetch")
            return {"error": "No driver provided"}

        logger.info(f"Fetching product info from: {self.url}")
        product_info = {}

        try:
            self.driver.get(self.url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "VU-ZEz"))
            )

            product_info['title'] = self._safe_get_text(By.CLASS_NAME, "VU-ZEz", default=None)
            product_info['price'] = self._safe_get_text(By.CSS_SELECTOR, "div.Nx9bqj.CxhGGd", default=None)
            product_info['rating'] = self._safe_get_text(By.CLASS_NAME, "XQDdHH", default=None)

            about_items = []
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "div.xFVion ul li")
                for el in elements:
                    try:
                        text = el.text.strip()
                        if text:
                            about_items.append(text)
                    except Exception as e:
                        logger.warning(f"Stale or inaccessible element in 'about_this_item': {e}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to locate 'about_this_item' elements: {e}")

            product_info['about_this_item'] = about_items

            services = self.driver.find_elements(By.CSS_SELECTOR, "ul.C3EUFP li div.YhUgfO")
            product_info['services'] = [item.text.strip() for item in services if item.text.strip()] or []

            para = self.driver.find_elements(By.CSS_SELECTOR, "div.yN\\+eNk.w9jEaj p")
            paragraphs = [p.text.strip() for p in para if p.text.strip()] or []
            product_info['paragraph'] = paragraphs

            product_info['technical_specifications'] = self._extract_tech_specs()
            product_info['rating_breakdown'] = self.extract_rating_breakdown()
            product_info['feature_ratings'] = self._extract_feature_ratings()
            logger.info(f"Product info fetched successfully")
            return product_info

        except TimeoutException:
            logger.warning("Title element not found, trying to fallback to body text")
            if "Robot Check" in self.driver.page_source:
                raise Exception("Blocked by Amazon - CAPTCHA or Robot Check page")
        except Exception as e:
            logger.exception("Unexpected error in fetch_product_info")
            product_info['error'] = str(e)

        return product_info

    def _safe_get_text(self, by: By, identifier: str, default: Optional[str] = None) -> Optional[str]:
        retries = 3
        for attempt in range(retries):
            try:
                element = self.driver.find_element(by, identifier)
                return element.text.strip()
            except StaleElementReferenceException:
                logger.warning(f"StaleElementReferenceException on attempt {attempt + 1}, retrying...")
                time.sleep(1)
            except NoSuchElementException:
                return default
            except Exception as e:
                logger.error(f"Unexpected error in _safe_get_text: {e}")
                return default
        return default

    def _extract_feature_ratings(self) -> Dict[str, float]:
        feature_ratings = {}

        try:
            # Select all <a> tags with the given exact class name
            rating_blocks = self.driver.find_elements(By.CSS_SELECTOR, 'a.col-3-12.zbCsdp.zsSYMX')

            for block in rating_blocks:
                try:
                    # Extract SVG <text> rating value
                    rating_elem = block.find_element(By.XPATH, ".//*[local-name()='text' and contains(@class, '_2DdnFS')]")
                    rating_text = rating_elem.text.strip()

                    # Extract label like "Camera"
                    label_elem = block.find_element(By.CSS_SELECTOR, "div.NTiEl0")
                    label_text = label_elem.text.strip()

                    if rating_text and label_text:
                        try:
                            feature_ratings[label_text] = float(rating_text)
                        except ValueError:
                            logger.warning(f"Non-numeric rating value: '{rating_text}' for label '{label_text}'")

                except Exception as inner_e:
                    logger.warning(f"Error parsing feature rating block: {inner_e}")
                    logger.debug(f"Block HTML:\n{block.get_attribute('innerHTML')}")

        except Exception as outer_e:
            logger.warning(f"Failed to extract feature ratings: {outer_e}")

        return feature_ratings

    def extract_rating_breakdown(self):
        rating_counts = {}
        try:
            logger.info("Waiting for rating breakdown section...")

            selector = 'ul.\\+psZUR li.fQ-FC1 div.BArk-j'

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )

            rating_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info(f"Found {len(rating_elements)} rating elements")

            for idx, element in enumerate(rating_elements):
                try:
                    star = 5 - idx  # Ratings are in order from 5★ to 1★
                    count_text = element.text.strip().replace(",", "")
                    logger.debug(f"Rating {star}★ raw text: '{element.text.strip()}' → cleaned: '{count_text}'")
                    rating_counts[star] = int(count_text) if count_text.isdigit() else 0
                except Exception as inner_e:
                    logger.warning(f"Failed to parse rating element at index {idx}: {inner_e}")
                    rating_counts[5 - idx] = 0

            logger.info(f"Extracted rating breakdown: {rating_counts}")

        except TimeoutException:
            logger.warning("Timeout while waiting for rating breakdown elements.")
        except Exception as e:
            logger.exception(f"Failed to extract rating breakdown: {e}")

        return rating_counts

    def _extract_tech_specs(self) -> Dict[str, str]:
        tech_specs = {}
        try:
            wait = WebDriverWait(self.driver, 10)

            logger.info("Waiting for technical specification container...")
            main_container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div._1OjC5I"))
            )
            logger.info("Found technical specification container.")

            first_section = main_container.find_element(By.CSS_SELECTOR, "div.GNDEQ-")
            logger.info("Found the first GNDEQ- section.")

            # Locate the table inside the first section
            table = first_section.find_element(By.CSS_SELECTOR, "table._0ZhAN9")
            rows = table.find_elements(By.TAG_NAME, "tr")

            if not rows:
                logger.warning("First table is empty.")
                return tech_specs

            for row in rows:
                try:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 2:
                        key = tds[0].text.strip()
                        value_cell = tds[1]

                        li_items = value_cell.find_elements(By.TAG_NAME, "li")
                        if li_items:
                            value = ", ".join(
                                li.text.strip() for li in li_items if li.text.strip()
                            )
                        else:
                            value = value_cell.text.strip()

                        if key and value:
                            tech_specs[key] = value
                except Exception as e:
                    logger.warning(f"Failed to parse row: {e}")

        except Exception as e:
            logger.warning(f"Failed to extract tech specs: {e}")

        return tech_specs

    def fetch_similar_items(self, product_title: str) -> List[Dict[str, Any]]:
        SERP_API_KEY = os.getenv("SERP_API_KEY")
        if not SERP_API_KEY or not product_title:
            logger.warning("Missing SERP_API_KEY or product title.")
            return []

        params = {
            "engine": "google",
            "q": product_title,
            "tbm": "shop",
            "api_key": SERP_API_KEY,
            "gl": "in",
            "hl": "en"
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            results = response.json().get("shopping_results", [])
            logger.info(f"Fetched {len(results)} similar items for '{product_title}'")

            return [
                {
                    "title": r.get("title"),
                    "price": r.get("price"),
                    "rating": r.get("rating"),
                    "reviews": r.get("reviews"),
                    "source": r.get("source"),
                    "link": r.get("link") or r.get("product_link") or "Link not available"
                }
                for r in results[:5]
            ]

        except Exception as e:
            logger.exception("Error fetching similar items")
            return []

    def fetch_youtube_videos(self, product_title: str) -> List[Dict[str, Any]]:
        SERP_API_KEY = os.getenv("SERP_API_KEY")
        if not SERP_API_KEY or not product_title:
            logger.warning("Missing SERP_API_KEY or product title for YouTube search.")
            return []

        params = {
            "engine": "youtube",
            "search_query": product_title,
            "api_key": SERP_API_KEY,
            "gl": "in",
            "hl": "en"
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            videos = response.json().get("video_results", [])
            logger.info(f"Fetched {len(videos)} YouTube videos for '{product_title}'")
            return [
                {
                    "title": v.get("title"),
                    "link": v.get("link"),
                    "channel": v.get("channel", {}).get("name"),
                    "published": v.get("published_date"),
                    "description": v.get("description")
                }
                for v in videos[:5]
            ]
        except Exception as e:
            logger.exception("Error fetching YouTube videos")
            return []
