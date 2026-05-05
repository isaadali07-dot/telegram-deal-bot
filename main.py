"""
🛒 UK Bargain Hunter Bot
Otomatik ucuz ürün bulucu - Car Boot Sale için
Platforms: eBay, Gumtree, Facebook Marketplace, Lost Property, Amazon Returns
"""

import os
import json
import time
import hashlib
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.ebay_scraper import scrape_ebay
from scrapers.gumtree_scraper import scrape_gumtree
from scrapers.lost_property_scraper import scrape_lost_property
from scrapers.amazon_returns_scraper import scrape_amazon_returns
from scrapers.facebook_scraper import scrape_facebook_rss

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# AYARLAR - bunları kendin düzenle
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Hangi platformlar aktif?
PLATFORMS_ENABLED = {
    "ebay": True,
    "gumtree": True,
    "facebook": True,
    "lost_property": True,
    "amazon_returns": True,
}

# Arama anahtar kelimeleri
SEARCH_KEYWORDS = [
    "vintage clothing",
    "retro electronics",
    "vinyl records",
    "job lot",
    "joblot",
    "bundle",
    "clearance",
    "collection",
    "wholesale",
    "car boot",
]

# Fiyat filtreleri (GBP)
MAX_PRICE = 50          # Maksimum alım fiyatı
MIN_PROFIT_RATIO = 2.0  # Minimum kar çarpanı (2x = %100 kar)

# Daha önce gönderilen ilanları takip etmek için
SEEN_FILE = "seen_ids.json"


# ─────────────────────────────────────────────
# TELEGRAM BİLDİRİM
# ─────────────────────────────────────────────
def send_telegram(message: str):
    """Telegram'a mesaj gönder."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram bilgileri eksik, bildirim gönderilmedi.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info("Telegram bildirimi gönderildi.")
    except Exception as e:
        log.error(f"Telegram hatası: {e}")


def format_alert(item: dict) -> str:
    """İlan için Telegram mesajı oluştur."""
    profit_emoji = "🔥" if item.get("profit_ratio", 1) >= 3 else "💰"
    platform_emoji = {
        "ebay": "🟡",
        "gumtree": "🟢",
        "facebook": "🔵",
        "lost_property": "✈️",
        "amazon_returns": "📦",
    }.get(item.get("platform", ""), "🛒")

    lines = [
        f"{profit_emoji} <b>YENİ FIRSAT BULUNDU!</b>",
        f"",
        f"{platform_emoji} Platform: <b>{item.get('platform', '?').upper()}</b>",
        f"📌 <b>{item.get('title', 'Başlık yok')}</b>",
        f"",
        f"💷 Satış Fiyatı: <b>£{item.get('price', '?')}</b>",
    ]

    if item.get("estimated_resale"):
        lines.append(f"📈 Tahmini Yeniden Satış: <b>£{item['estimated_resale']}</b>")

    if item.get("profit_ratio"):
        lines.append(f"🎯 Kar Çarpanı: <b>{item['profit_ratio']:.1f}x</b>")

    if item.get("location"):
        lines.append(f"📍 Konum: {item['location']}")

    if item.get("condition"):
        lines.append(f"🔎 Durum: {item['condition']}")

    if item.get("url"):
        lines.append(f"")
        lines.append(f"🔗 <a href=\"{item['url']}\">İlana Git →</a>")

    lines.append(f"")
    lines.append(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# GÖRÜLMÜŞ İLAN TAKİBİ
# ─────────────────────────────────────────────
def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def make_id(item: dict) -> str:
    key = f"{item.get('platform')}_{item.get('url', item.get('title', ''))}"
    return hashlib.md5(key.encode()).hexdigest()


# ─────────────────────────────────────────────
# KAR TAHMİNİ
# ─────────────────────────────────────────────
RESALE_MULTIPLIERS = {
    "vintage": 4.0,
    "vinyl": 5.0,
    "retro": 3.5,
    "brand": 3.0,
    "electronics": 2.5,
    "clothing": 2.5,
    "toy": 2.0,
    "book": 1.5,
    "default": 2.0,
}

def estimate_profit(item: dict) -> dict:
    title_lower = item.get("title", "").lower()
    multiplier = RESALE_MULTIPLIERS["default"]

    for keyword, mult in RESALE_MULTIPLIERS.items():
        if keyword in title_lower:
            multiplier = mult
            break

    try:
        price = float(str(item.get("price", "0")).replace("£", "").replace(",", "").strip())
        estimated_resale = round(price * multiplier, 2)
        item["estimated_resale"] = estimated_resale
        item["profit_ratio"] = multiplier
        item["price"] = price
    except:
        item["profit_ratio"] = 1.0

    return item


# ─────────────────────────────────────────────
# ANA DÖNGÜ
# ─────────────────────────────────────────────
def run():
    log.info("🚀 Bargain Hunter başlatıldı...")
    seen = load_seen()
    all_items = []

    # Platform tarayıcılarını çalıştır
    scrapers = []
    if PLATFORMS_ENABLED.get("ebay"):
        scrapers.append(("ebay", scrape_ebay))
    if PLATFORMS_ENABLED.get("gumtree"):
        scrapers.append(("gumtree", scrape_gumtree))
    if PLATFORMS_ENABLED.get("facebook"):
        scrapers.append(("facebook", scrape_facebook_rss))
    if PLATFORMS_ENABLED.get("lost_property"):
        scrapers.append(("lost_property", scrape_lost_property))
    if PLATFORMS_ENABLED.get("amazon_returns"):
        scrapers.append(("amazon_returns", scrape_amazon_returns))

    for platform_name, scraper_func in scrapers:
        try:
            log.info(f"🔍 {platform_name} taranıyor...")
            items = scraper_func(SEARCH_KEYWORDS, max_price=MAX_PRICE)
            for item in items:
                item["platform"] = platform_name
            all_items.extend(items)
            log.info(f"✅ {platform_name}: {len(items)} ilan bulundu.")
        except Exception as e:
            log.error(f"❌ {platform_name} hatası: {e}")

    # Yeni ilanları filtrele ve bildir
    new_count = 0
    for item in all_items:
        item = estimate_profit(item)
        item_id = make_id(item)

        if item_id in seen:
            continue

        # Fiyat kontrolü
        price = item.get("price", 999)
        if isinstance(price, (int, float)) and price > MAX_PRICE:
            continue

        # Kar filtresi
        if item.get("profit_ratio", 1.0) < MIN_PROFIT_RATIO:
            continue

        # Telegram bildirimi
        message = format_alert(item)
        send_telegram(message)
        seen.add(item_id)
        new_count += 1
        time.sleep(1)  # Telegram rate limit

    save_seen(seen)
    log.info(f"✅ Tamamlandı. {new_count} yeni ilan bildirildi.")

    if new_count == 0:
        log.info("Yeni uygun ilan bulunamadı.")


if __name__ == "__main__":
    run()
