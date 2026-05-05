"""
Facebook Marketplace Scraper
Facebook Marketplace direkt scraping yasal sorunlar çıkarabileceğinden,
bu modül RSS alternatifleri ve resmi yöntemleri kullanır.

Alternatif kaynaklar:
- Facebook Public RSS (meta tag üzerinden)  
- Nextdoor (yerel topluluk ilanları)
- Preloved.co.uk (UK'nın en büyük ikinci el platformu)
- Freecycle (ücretsiz eşyalar)
"""

import re
import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

# Facebook yerine kullanılabilecek açık platformlar
OPEN_PLATFORMS = [
    {
        "name": "Preloved UK",
        "search_url": "https://www.preloved.co.uk/classifieds/all/uk/+{keyword}?price_to={max_price}",
        "type": "html",
    },
    {
        "name": "Freecycle Network",
        "rss_url": "https://groups.freecycle.org/group/LondonUK/rss",
        "type": "rss",
    },
    {
        "name": "Freegle",
        "search_url": "https://www.ilovefreegle.org/explore",
        "type": "html",
    },
]


def scrape_facebook_rss(keywords: list, max_price: float = 50) -> list:
    """
    Facebook Marketplace'in doğrudan scraping'i TOS ihlalidir.
    Bunun yerine eşdeğer açık UK platformlarını tarar.
    
    Facebook Marketplace için manuel yöntem:
    1. marketplace.facebook.com adresine git
    2. Arama yap, filtrele
    3. Sonuçları Telegram'a kendin ekle
    """
    all_items = []

    # Preloved UK tara
    for keyword in keywords[:3]:
        try:
            items = _scrape_preloved(keyword, max_price)
            all_items.extend(items)
        except Exception as e:
            log.warning(f"Preloved '{keyword}' hatası: {e}")

    # Freecycle RSS tara (ücretsiz eşyalar = saf kar)
    try:
        free_items = _scrape_freecycle_rss()
        all_items.extend(free_items)
    except Exception as e:
        log.warning(f"Freecycle hatası: {e}")

    # FB Marketplace bilgi kartı ekle
    all_items.append(_facebook_manual_tip())

    return all_items


def _scrape_preloved(keyword: str, max_price: float) -> list:
    """Preloved.co.uk arama."""
    url = f"https://www.preloved.co.uk/classifieds/all/uk/+{keyword.replace(' ', '+')}"
    params = {"price_to": int(max_price), "sort": "date_desc"}

    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    listings = soup.find_all(class_=re.compile(r"advert|listing|item", re.I))[:8]

    for listing in listings:
        try:
            title_el = listing.find(["h2", "h3", "a"])
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            price_el = listing.find(class_=re.compile(r"price", re.I))
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)
            if price is None or price > max_price:
                continue

            link_el = listing.find("a", href=True)
            path = link_el["href"] if link_el else ""
            full_url = f"https://www.preloved.co.uk{path}" if path.startswith("/") else path

            results.append({
                "title": f"🔵 [Preloved] {title}",
                "price": price,
                "url": full_url,
                "location": "UK",
                "condition": "Second Hand",
                "source": "preloved",
            })
        except Exception as e:
            log.debug(f"Preloved parse hatası: {e}")

    return results


def _scrape_freecycle_rss() -> list:
    """Freecycle RSS - tamamen ücretsiz eşyalar."""
    results = []
    rss_urls = [
        "https://groups.freecycle.org/group/LondonUK/rss",
        "https://groups.freecycle.org/group/BirminghamUK/rss",
        "https://groups.freecycle.org/group/ManchesterUK/rss",
    ]

    for rss_url in rss_urls[:2]:
        try:
            r = requests.get(rss_url, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.content)
            channel = root.find("channel")
            if not channel:
                continue

            for item in channel.findall("item")[:5]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")

                # Sadece OFFER (teklif) ilanları - WANTED değil
                if "OFFER" in title.upper() or "offer" in desc.lower():
                    results.append({
                        "title": f"🆓 [BEDAVA] {title}",
                        "price": 0.0,
                        "estimated_resale": 10.0,
                        "profit_ratio": 999,
                        "url": link,
                        "location": "UK",
                        "condition": "Free - Condition Unknown",
                        "source": "freecycle",
                    })
        except Exception as e:
            log.debug(f"Freecycle RSS hatası: {e}")

    return results


def _facebook_manual_tip() -> dict:
    """Facebook Marketplace için manuel kontrol hatırlatıcısı."""
    return {
        "title": "🔵 [HATIRLATICI] Facebook Marketplace Manuel Kontrol",
        "price": 0.0,
        "url": "https://www.facebook.com/marketplace/london/",
        "location": "Facebook Marketplace",
        "condition": "Manuel Kontrol Gerekli",
        "source": "facebook_tip",
        "notes": (
            "Facebook Marketplace'i manuel tara:\n"
            "Filtreler: 'Free' veya £0-£20, Sort: Newest\n"
            "Kategoriler: Electronics, Clothing, Garden"
        ),
    }


def _parse_price(price_text: str) -> float | None:
    if not price_text:
        return None
    if "free" in price_text.lower():
        return 0.0
    match = re.search(r"£?([\d,]+\.?\d*)", price_text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None
