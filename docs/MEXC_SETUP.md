# 🚀 LeviBot Enterprise - MEXC Entegrasyonu

> **MEXC exchange için özel kurulum ve konfigürasyon rehberi**

---

## 📋 MEXC API Key Nasıl Alınır?

### 1. MEXC Hesabı Oluştur

1. [MEXC Global](https://www.mexc.com) adresine git
2. Hesap oluştur ve KYC'yi tamamla
3. 2FA (Two-Factor Authentication) aktif et

### 2. API Key Oluştur

1. MEXC'de oturum aç
2. **Account** → **API Management** → **Create API**
3. API Key adı gir (örn: "LeviBot Paper Trading")
4. **Permissions** seç:
   - ✅ **Read** (zorunlu)
   - ✅ **Spot Trading** (paper mode için)
   - ❌ **Withdraw** (güvenlik için kapalı)
5. 2FA kodunu gir
6. **API Key** ve **Secret Key**'i kopyala

### 3. IP Whitelist (Opsiyonel ama Önerilen)

1. API Management'ta oluşturduğun key'i seç
2. **Edit** → **IP Whitelist**
3. Sunucu IP'ni ekle (örn: `123.45.67.89`)
4. Veya development için `0.0.0.0/0` (tüm IP'ler - sadece test için!)

---

## ⚙️ Environment Konfigürasyonu

### `.env` Dosyası

```bash
# EXCHANGE (MEXC)
EXCHANGE=mexc
MARKET_TYPE=spot
MEXC_API_KEY=mx0vglABCDEFGHIJKLMNOPQRSTUVWXYZ
MEXC_SECRET=1234567890abcdef1234567890abcdef1234567890abcdef
MEXC_TESTNET=false

# SYMBOLS (MEXC Spot)
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,ADAUSDT,DOGEUSDT,XRPUSDT
```

---

## 🎯 MEXC Özellikleri

### Desteklenen Market Türleri

- ✅ **Spot Trading** (ana pazar)
- ✅ **Futures** (kaldıraçlı işlemler)
- ❌ **Margin** (henüz desteklenmiyor)

### Rate Limits

- **REST API:** 20 requests/second
- **WebSocket:** 10 connections/IP
- **Order Placement:** 100 orders/10 seconds

### Minimum Order Sizes

| Symbol  | Min Notional | Min Quantity |
| ------- | ------------ | ------------ |
| BTCUSDT | 5 USDT       | 0.00001 BTC  |
| ETHUSDT | 5 USDT       | 0.0001 ETH   |
| SOLUSDT | 5 USDT       | 0.01 SOL     |
| BNBUSDT | 5 USDT       | 0.001 BNB    |

---

## 🔧 CCXT Konfigürasyonu

LeviBot, CCXT kütüphanesi üzerinden MEXC'ye bağlanır:

```python
import ccxt

exchange = ccxt.mexc({
    'apiKey': os.getenv('MEXC_API_KEY'),
    'secret': os.getenv('MEXC_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',  # veya 'future'
        'adjustForTimeDifference': True,
    }
})
```

### Test Bağlantısı

```bash
# Python shell'de test et
cd backend
python3 << EOF
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.mexc({
    'apiKey': os.getenv('MEXC_API_KEY'),
    'secret': os.getenv('MEXC_SECRET'),
    'enableRateLimit': True,
})

# Balance kontrolü
balance = exchange.fetch_balance()
print(f"USDT Balance: {balance['USDT']['free']}")

# Market data test
ticker = exchange.fetch_ticker('BTC/USDT')
print(f"BTC/USDT Price: {ticker['last']}")
EOF
```

---

## 📊 Paper Trading vs Real Trading

### Paper Mode (Önerilen Başlangıç)

```bash
# .env
ENV=paper
EXCHANGE=mexc
MEXC_API_KEY=your_key_here  # Read-only yeterli
MEXC_SECRET=your_secret_here
```

**Özellikler:**

- ✅ Gerçek market data
- ✅ Simüle edilmiş emirler
- ✅ Risk yok
- ✅ Stratejileri test et

### Real Mode (Production)

```bash
# .env
ENV=production
EXCHANGE=mexc
MEXC_API_KEY=your_key_here  # Trading permission gerekli
MEXC_SECRET=your_secret_here

# Risk limitleri
PER_TRADE_RISK=0.002  # %0.2 (daha düşük)
DAILY_DD_STOP=0.02    # %2 (daha sıkı)
MAX_DAILY_TRADES=30   # Daha az trade
```

**Uyarılar:**

- ⚠️ Küçük sermaye ile başla (örn: $100-500)
- ⚠️ İlk 7 gün paper mode'da test et
- ⚠️ Stop-loss'ları mutlaka kullan
- ⚠️ Kill-switch'i test et

---

## 🔍 MEXC Spesifik Ayarlar

### 1. Symbol Format

MEXC'de semboller **slash olmadan** yazılır:

```python
# Doğru
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

# Yanlış (Binance formatı)
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
```

### 2. Timestamp Sync

MEXC, timestamp hassasiyeti konusunda katıdır:

```bash
# .env
MEXC_ADJUST_FOR_TIME_DIFFERENCE=true
```

### 3. Order Types

Desteklenen emir türleri:

- ✅ **LIMIT** - Limit emir
- ✅ **MARKET** - Market emir
- ✅ **STOP_LOSS** - Stop loss
- ✅ **STOP_LOSS_LIMIT** - Stop loss limit
- ✅ **TAKE_PROFIT** - Take profit
- ✅ **TAKE_PROFIT_LIMIT** - Take profit limit

### 4. WebSocket Streams

```python
# OHLCV stream
ws_url = 'wss://wbs.mexc.com/ws'
subscribe = {
    "method": "SUBSCRIPTION",
    "params": ["spot@public.kline.v3.api@BTCUSDT@Min1"]
}
```

---

## 🧪 Test Senaryoları

### 1. Balance Check

```bash
curl -X GET "https://api.mexc.com/api/v3/account" \
  -H "X-MEXC-APIKEY: your_api_key"
```

### 2. Market Data

```bash
curl "https://api.mexc.com/api/v3/ticker/24hr?symbol=BTCUSDT"
```

### 3. Place Order (Test)

```bash
# Paper mode'da bu gerçek emir göndermez
curl -X POST "https://api.mexc.com/api/v3/order/test" \
  -H "X-MEXC-APIKEY: your_api_key" \
  -d "symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=0.001&price=60000"
```

---

## 🚨 Sık Karşılaşılan Hatalar

### 1. "Invalid API Key"

**Çözüm:**

- API Key'i doğru kopyaladığından emin ol
- Boşluk veya özel karakter olmadığını kontrol et
- API Key'in aktif olduğunu doğrula

### 2. "Timestamp for this request is outside of the recvWindow"

**Çözüm:**

```bash
# Sistem saatini senkronize et
sudo ntpdate -s time.nist.gov

# veya .env'de
MEXC_ADJUST_FOR_TIME_DIFFERENCE=true
```

### 3. "Insufficient balance"

**Çözüm:**

- MEXC hesabında yeterli USDT olduğundan emin ol
- Minimum order size'ı kontrol et (5 USDT)
- Paper mode'da başlangıç sermayesi: `PAPER_STARTING_BALANCE=10000`

### 4. "Rate limit exceeded"

**Çözüm:**

```bash
# .env
MEXC_RATE_LIMIT_ENABLED=true
MEXC_RATE_LIMIT_DELAY=50  # ms
```

### 5. "Symbol not found"

**Çözüm:**

```bash
# Desteklenen sembolleri listele
curl "https://api.mexc.com/api/v3/exchangeInfo" | jq '.symbols[].symbol'
```

---

## 📈 Önerilen Başlangıç Konfigürasyonu

### Conservative (Güvenli)

```bash
# .env
ENV=paper
EXCHANGE=mexc
SYMBOLS=BTCUSDT,ETHUSDT

# Risk
PER_TRADE_RISK=0.001      # %0.1
DAILY_DD_STOP=0.01        # %1
MAX_DAILY_TRADES=10
COOLDOWN_MINUTES=15

# ML
MIN_CONFIDENCE=0.65       # Yüksek eşik
```

### Moderate (Dengeli)

```bash
# .env
ENV=paper
EXCHANGE=mexc
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT

# Risk
PER_TRADE_RISK=0.002      # %0.2
DAILY_DD_STOP=0.02        # %2
MAX_DAILY_TRADES=25
COOLDOWN_MINUTES=10

# ML
MIN_CONFIDENCE=0.58       # Orta eşik
```

### Aggressive (Agresif)

```bash
# .env
ENV=paper
EXCHANGE=mexc
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,ADAUSDT,DOGEUSDT

# Risk
PER_TRADE_RISK=0.003      # %0.3
DAILY_DD_STOP=0.03        # %3
MAX_DAILY_TRADES=50
COOLDOWN_MINUTES=5

# ML
MIN_CONFIDENCE=0.52       # Düşük eşik
```

---

## 🔐 Güvenlik Best Practices

1. **API Key Permissions:**

   - ✅ Read + Spot Trading
   - ❌ Withdraw (asla açma!)

2. **IP Whitelist:**

   - Production'da mutlaka kullan
   - VPS IP'sini ekle

3. **2FA:**

   - Her zaman aktif tut
   - API işlemleri için zorunlu

4. **Secret Rotation:**

   - 30 günde bir API key'i yenile
   - Eski key'i devre dışı bırak

5. **Monitoring:**
   - API kullanımını izle
   - Anormal aktivite için alert kur

---

## 📚 Faydalı Linkler

- [MEXC API Documentation](https://mexcdevelop.github.io/apidocs/spot_v3_en/)
- [MEXC WebSocket Documentation](https://mexcdevelop.github.io/apidocs/spot_v3_en/#websocket-market-data)
- [CCXT MEXC Documentation](https://docs.ccxt.com/#/exchanges/mexc)
- [MEXC Trading Fees](https://www.mexc.com/fee)
- [MEXC Support](https://www.mexc.com/support)

---

## 🎯 Sonraki Adımlar

1. ✅ MEXC API Key al
2. ✅ `.env` dosyasını doldur
3. ✅ Test bağlantısı yap
4. ✅ Paper mode'da 7 gün test et
5. ✅ Performance metriklerini analiz et
6. ✅ Production'a geç (küçük sermaye ile)

---

<p align="center">
  <strong>🚀 MEXC ile LeviBot Enterprise - Hazırsın! 🚀</strong><br>
  <em>Hayırlı kazançlar paşam! 💰</em>
</p>
