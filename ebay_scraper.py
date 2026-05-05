"""
eBay UK Scraper
eBay Finding API'yi kullanarak ucuz ilanları tarar.
Ücretsiz eBay Developer hesabı gerektirir: https://developer.ebay.com
"""

import os
import requests
import logging

log = logging.getLogger(__name__)

EBAY_APP_ID = os.environ.get("EBAY_APP_ID", "")  # eBay API key
EBAY_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"


def scrape_ebay(keywords: list, max_price: float = 50) -> list:
    """
    eBay'de ucuz ilanları ara.
    API key yoksa RSS feed fallback kullanır.
    """
    items = []

    for keyword in keywords[:5]:  # İlk 5 kelimeyi tara
        try:
            if EBAY_APP_ID:
                results = _search_ebay_api(keyword, max_price)
            else:
                results = _search_ebay_rss(keyword, max_price)
            items.extend(results)
        except Exception as e:
            log.error(f"eBay '{keyword}' hatası: {e}")

    return items


def _search_ebay_api(keyword: str, max_price: float) -> list:
    """eBay resmi Finding API ile arama."""
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "keywords": keyword,
        "itemFilter(0).name": "MaxPrice",
        "itemFilter(0).value": str(max_price),
        "itemFilter(0).paramName": "Currency",
        "itemFilter(0).paramValue": "GBP",
        "itemFilter(1).name": "ListingType",
        "itemFilter(1).value": "FixedPrice",
        "itemFilter(2).name": "LocatedIn",
        "itemFilter(2).value": "GB",
        "sortOrder": "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": "10",
    }

    r = requests.get(EBAY_API_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = []
    search_result = data.get("findItemsAdvancedResponse", [{}])[0]
    items_list = search_result.get("searchResult", [{}])[0].get("item", [])

    for item in items_list:
        try:
            price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
            results.append({
                "title": item["title"][0],
                "price": price,
                "url": item["viewItemURL"][0],
                "condition": item.get("condition", [{}])[0].get("conditionDisplayName", [""])[0],
                "location": item.get("location", ["UK"])[0],
                "source": "ebay_api",
            })
        except Exception as e:
            log.debug(f"eBay item parse hatası: {e}")

    return results


def _search_ebay_rss(keyword: str, max_price: float) -> list:
    """
    eBay RSS feed fallback (API key gerektirmez).
    eBay'in herkese açık RSS'ini kullanır.
    """
    import xml.etree.ElementTree as ET

    url = (
        f"https://www.ebay.co.uk/srh/srh?keyword={keyword.replace(' ', '+')}"
        f"&sacat=0&LH_BIN=1&_sop=15&_stpos=&_pgn=1"
    )

    # eBay arama RSS - gerçek URL formatı
    rss_url = (
        f"https://www.ebay.co.uk/rss/buyersseller?keyword={keyword.replace(' ', '%20')}"
        f"&format=rss&LH_BIN=1&LH_PrefLoc=1&_sop=15"
    )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; BargainBot/1.0)"}
    r = requests.get(rss_url, headers=headers, timeout=10)

    results = []
    try:
        root = ET.fromstring(r.content)
        ns = {"media": "http://search.yahoo.com/mrss/"}
        channel = root.find("channel")

        for i_item in (channel.findall("item") if channel else [])[:10]:
            title = i_item.findtext("title", "")
            link = i_item.findtext("link", "")
            desc = i_item.findtext("description", "")

            # Fiyatı description'dan çıkarmaya çalış
            import re
            price_match = re.search(r"£([\d,]+\.?\d*)", desc)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0

            if price and price <= max_price:
                results.append({
                    "title": title,
                    "price": price,
                    "url": link,
                    "condition": "Used",
                    "location": "UK",
                    "source": "ebay_rss",
                })
    except Exception as e:
        log.error(f"eBay RSS parse hatası: {e}")

    return results
