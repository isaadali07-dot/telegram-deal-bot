"""
Amazon İade Paleti Scraper
UK'daki Amazon iade paleti satıcılarını tarar.

Yasal kaynaklar:
- B-Stock Solutions (Amazon'un resmi iade kanalı)
- Liquidation.com
- TopDown Trading
- Pallet2Cash
- Return Helper UK
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

# Amazon iade paleti kaynakları
RETURN_SOURCES = [
    {
        "name": "B-Stock Amazon UK",
        "url": "https://bstock.com/amazon/",
        "description": "Amazon'un resmi toplu iade açık artırma platformu",
        "min_lot": 100,
        "type": "auction",
    },
    {
        "name": "Liquidation.com UK",
        "url": "https://www.liquidation.com/search.html?p=amazon+returns&country=UK",
        "description": "Amazon ve diğer perakendecilerin iade paletleri",
        "min_lot": 50,
        "type": "auction",
    },
    {
        "name": "TopDown Trading",
        "url": "https://www.topdowntrading.co.uk/collections/amazon-return-pallets",
        "description": "UK tabanlı Amazon iade paleti satıcısı",
        "min_lot": 30,
        "type": "fixed_price",
    },
    {
        "name": "Pallet2Cash",
        "url": "https://pallet2cash.co.uk/product-category/amazon-returns/",
        "description": "Amazon iade paletleri - küçük lotlar mevcut",
        "min_lot": 20,
        "type": "fixed_price",
    },
]


def scrape_amazon_returns(keywords: list, max_price: float = 200) -> list:
    """
    Amazon iade paleti ilanlarını tara.
    max_price burada palet fiyatı için daha yüksek olabilir.
    """
    all_items = []

    # Sabit fiyatlı siteleri tara
    for source in RETURN_SOURCES:
        try:
            if source["type"] == "fixed_price":
                items = _scrape_fixed_price(source, max_price)
            else:
                items = _get_auction_info(source)
            all_items.extend(items)
            log.info(f"Amazon Returns '{source['name']}': {len(items)} ilan")
        except Exception as e:
            log.warning(f"Amazon Returns '{source['name']}' hatası: {e}")

    # Scraping başarısız olursa bilgilendirici kartlar döndür
    if not all_items:
        all_items = _get_platform_info_cards()

    return all_items


def _scrape_fixed_price(source: dict, max_price: float) -> list:
    """Sabit fiyatlı palet sitelerini tara."""
    results = []

    r = requests.get(source["url"], headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # WooCommerce / Shopify ürün kartları
    products = soup.find_all(
        class_=re.compile(r"product|item|card|listing", re.I)
    )[:10]

    for product in products:
        try:
            title_el = product.find(["h2", "h3", "h4", "a"])
            title = title_el.get_text(strip=True) if title_el else ""
            if not title or len(title) < 5:
                continue

            price_el = product.find(class_=re.compile(r"price|amount|cost", re.I))
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)

            if price is None:
                continue

            link_el = product.find("a", href=True)
            url = link_el["href"] if link_el else source["url"]
            if url.startswith("/"):
                base = "/".join(source["url"].split("/")[:3])
                url = base + url

            # Palet değer tahmini (genellikle 3-5x iade değeri)
            estimated_value = price * 3.5

            results.append({
                "title": f"📦 [Amazon İade] {title}",
                "price": price,
                "estimated_resale": round(estimated_value, 2),
                "profit_ratio": 3.5,
                "url": url,
                "location": "UK Warehouse",
                "condition": "Amazon Returns - Mixed Condition",
                "source": source["name"],
            })
        except Exception as e:
            log.debug(f"Product parse hatası: {e}")

    return results


def _get_auction_info(source: dict) -> list:
    """Açık artırma sitesi için bilgi kartı."""
    return [{
        "title": f"📦 {source['name']} - Aktif Açık Artırmalar",
        "price": source["min_lot"],
        "estimated_resale": source["min_lot"] * 3,
        "profit_ratio": 3.0,
        "url": source["url"],
        "location": "UK",
        "condition": "Amazon Returns Pallet",
        "source": source["name"],
        "notes": source["description"],
    }]


def _get_platform_info_cards() -> list:
    """
    Gerçek scraping yokken, kullanıcıya kaynak bilgisi ver.
    """
    return [
        {
            "title": "📦 B-Stock Amazon UK - En Ucuz Resmi Kanal",
            "price": 100.0,
            "estimated_resale": 400.0,
            "profit_ratio": 4.0,
            "url": "https://bstock.com/amazon/",
            "location": "UK Fulfillment Centers",
            "condition": "Amazon Returns - Mixed",
            "source": "bstock_info",
            "notes": "Amazon'un tek resmi iade kanalı. Kayıt ücretsiz.",
        },
        {
            "title": "📦 TopDown Trading - Küçük Lot Fashion Returns",
            "price": 30.0,
            "estimated_resale": 120.0,
            "profit_ratio": 4.0,
            "url": "https://www.topdowntrading.co.uk",
            "location": "UK",
            "condition": "Grade A/B Returns",
            "source": "topdown_info",
            "notes": "£30'dan başlayan moda iade lotları. Car boot için ideal.",
        },
    ]


def _parse_price(price_text: str) -> float | None:
    if not price_text:
        return None
    match = re.search(r"£?([\d,]+\.?\d*)", price_text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None
