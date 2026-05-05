"""
Gumtree UK Scraper
Gumtree'de ücretsiz ve ucuz ilanları tarar.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

GUMTREE_BASE = "https://www.gumtree.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}


def scrape_gumtree(keywords: list, max_price: float = 50) -> list:
    """Gumtree'de anahtar kelime araması yapar."""
    all_items = []

    for keyword in keywords[:4]:
        try:
            items = _search_gumtree(keyword, max_price)
            all_items.extend(items)
            log.info(f"Gumtree '{keyword}': {len(items)} ilan")
        except Exception as e:
            log.error(f"Gumtree '{keyword}' hatası: {e}")

    return all_items


def _search_gumtree(keyword: str, max_price: float) -> list:
    """Tek bir anahtar kelime için Gumtree araması."""
    url = (
        f"{GUMTREE_BASE}/search"
        f"?search_category=all"
        f"&q={keyword.replace(' ', '+')}"
        f"&search_location=uk"
        f"&max_price={int(max_price)}"
        f"&sort=date"
    )

    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        log.warning(f"Gumtree HTTP {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    # Gumtree ilan kartları
    listings = soup.find_all("article", class_=re.compile(r"listing-maxi|natural-listing"))

    for listing in listings[:10]:
        try:
            # Başlık
            title_el = listing.find(["h2", "h3", "a"], class_=re.compile(r"listing-title|title"))
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            # Link
            link_el = listing.find("a", href=True)
            url_path = link_el["href"] if link_el else ""
            full_url = f"{GUMTREE_BASE}{url_path}" if url_path.startswith("/") else url_path

            # Fiyat
            price_el = listing.find(class_=re.compile(r"price|listing-price"))
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)

            if price is None or price > max_price:
                continue

            # Konum
            loc_el = listing.find(class_=re.compile(r"location"))
            location = loc_el.get_text(strip=True) if loc_el else "UK"

            results.append({
                "title": title,
                "price": price,
                "url": full_url,
                "location": location,
                "condition": "Used",
                "source": "gumtree",
            })

        except Exception as e:
            log.debug(f"Gumtree ilan parse hatası: {e}")

    return results


def _parse_price(price_text: str) -> float | None:
    """Fiyat metnini float'a çevir."""
    if not price_text:
        return None

    price_text = price_text.lower()

    if "free" in price_text:
        return 0.0

    match = re.search(r"£?([\d,]+\.?\d*)", price_text)
    if match:
        return float(match.group(1).replace(",", ""))

    return None
