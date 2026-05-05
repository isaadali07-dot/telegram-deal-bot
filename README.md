# 🛒 UK Bargain Hunter Bot

Car Boot Sale için otomatik fırsat bulucu.  
5 platformu tarar, kar hesaplar, Telegram'a bildirir.

---

## 📱 Nasıl Çalışır?

```
Her 30 dakika
     ↓
GitHub Actions çalışır (ücretsiz sunucu)
     ↓
eBay + Gumtree + Preloved + Kayıp Eşya + Amazon Returns taranır
     ↓
Fiyat & kar filtresi uygulanır
     ↓
Yeni ilanlar Telegram'a gönderilir
     ↓
Sen sadece telefona bakarsın 📱
```

---

## 🚀 KURULUM (Adım Adım)

### 1. Telegram Bot Oluştur (5 dakika)

1. Telegram'da **@BotFather**'ı aç
2. `/newbot` yaz
3. Bot ismi ver (örn: `UKBargainBot`)
4. Sana verilen **TOKEN**'ı kopyala (şuna benzer: `7123456789:AAFxxx...`)

### 2. Chat ID'ni Öğren

1. Yeni botuna bir mesaj gönder (herhangi bir şey)
2. Şu linki tarayıcıda aç:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   `<TOKEN>` yerine botun token'ını yaz
3. Çıkan JSON'da `"chat":{"id":` yazan sayıyı kopyala → Bu senin **CHAT_ID**'n

### 3. GitHub'a Yükle

1. [github.com](https://github.com) hesabı aç (ücretsiz)
2. **New Repository** → İsim ver → Public
3. Bu klasördeki tüm dosyaları yükle (drag & drop)

### 4. Gizli Anahtarları Gir

GitHub repo sayfasında:
```
Settings → Secrets and variables → Actions → New repository secret
```

Şunları ekle:

| İsim | Değer |
|------|-------|
| `TELEGRAM_TOKEN` | BotFather'dan aldığın token |
| `TELEGRAM_CHAT_ID` | Yukarıda bulduğun chat ID |
| `EBAY_APP_ID` | (Opsiyonel) eBay API key |

### 5. Actions'ı Aktif Et

1. GitHub repo → **Actions** sekmesi
2. **"I understand my workflows..."** → Enable
3. Sol menüden **Bargain Hunter** → **Run workflow** → Test et!

---

## ⚙️ AYARLAR (main.py)

```python
MAX_PRICE = 50          # Maksimum alım fiyatı (£)
MIN_PROFIT_RATIO = 2.0  # Minimum 2x kar (£10 al, £20+ sat)

SEARCH_KEYWORDS = [
    "vintage clothing",
    "vinyl records",
    "retro electronics",
    # kendi anahtar kelimelerini ekle
]
```

---

## 📊 Telegram Bildirimi Nasıl Görünür?

```
🔥 YENİ FIRSAT BULUNDU!

🟡 Platform: EBAY
📌 Vintage Levi's Denim Jacket Bundle x5

💷 Satış Fiyatı: £15
📈 Tahmini Yeniden Satış: £60
🎯 Kar Çarpanı: 4.0x
📍 Konum: Manchester, UK
🔎 Durum: Used

🔗 İlana Git →

⏰ 12/05/2025 09:30
```

---

## 🏪 Takip Edilen Platformlar

| Platform | Ne Tarar? | Kar Potansiyeli |
|----------|-----------|-----------------|
| **eBay UK** | Düşük fiyatlı ilanlar | ★★★★ |
| **Gumtree** | Yerel ilanlar, bedavalar | ★★★★★ |
| **Preloved UK** | İkinci el genel | ★★★ |
| **Freecycle** | Tamamen bedava eşyalar | ★★★★★ |
| **Lost Property** | Havalimanı açık artırmaları | ★★★ |
| **Amazon Returns** | İade paletleri | ★★★★ |

---

## 💡 Pro İpuçları

### En Karlı Kategoriler:
- 👗 Vintage giysi (4-5x kar)
- 🎵 Vinil plaklar (5x+ kar)
- 🎮 Retro elektronik (3-4x kar)
- 📱 Küçük elektronik (2-3x kar)
- 🧸 Marka oyuncaklar (2-3x kar)

### En İyi Satış Platformları:
- **eBay** → Genel, geniş kitle
- **Depop** → Vintage giysi
- **Vinted** → Günlük giysi
- **Facebook Marketplace** → Büyük/ağır eşyalar

---

## ❓ Sık Sorulan Sorular

**S: GitHub Actions ne kadar ücretsiz?**  
Her ay 2000 dakika ücretsiz. Her çalışma ~2 dakika = ayda 1000 çalışma. Yeterli!

**S: eBay API key gerekli mi?**  
Hayır. API key olmadan RSS feed kullanır. Ama API key ile daha iyi sonuçlar alırsın.  
Ücretsiz al: https://developer.ebay.com

**S: Facebook Marketplace neden tam otomatik değil?**  
Facebook scraping Terms of Service ihlali. Preloved ve Freecycle gibi açık alternatifler kullanılıyor.

---

## 📞 Destek

Sorun yaşarsan GitHub Issues bölümüne yaz.
