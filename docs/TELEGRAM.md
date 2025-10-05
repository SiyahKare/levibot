# Telegram Sinyal Entegrasyonu

Bu modül iki kaynaktan sinyal toplayabilir:
- Bot API (aiogram): gruba eklenen bot mesajları yakalar.
- User-bot (Telethon): kendi hesabınla üye olduğun chat’leri okur; otomatik keşif + backfill + canlı akış destekler.

## Hızlı Kurulum

1) .env
```
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_SESSION_PATH=telegram/sessions/onur.session
# Whitelist / Discovery
TELEGRAM_ALLOWED_CHATS=
TELEGRAM_AUTO_DISCOVER=true
TELEGRAM_ALLOW_PATTERNS=alpha,signal,trade,scalp
TELEGRAM_DENY_PATTERNS=sohbet,chat,random
TELEGRAM_INCLUDE_DM=false
# Backfill
TELEGRAM_STARTUP_HISTORY_LIMIT=200
TELEGRAM_CHECKPOINTS_PATH=telegram/checkpoints.json
```

2) Başlat
```
python3 -m telegram.user_client
```
İlk çalıştırmada telefon doğrulaması ister; session dosyası `telegram/sessions/` altında oluşur.

## Çalışma Prensibi
- Keşif: ALLOWED boşsa AUTO_DISCOVER ile başlık/username pattern’lerine uyan chat’ler seçilir.
- Backfill: Başlangıçta her chat için son STARTUP_HISTORY_LIMIT mesaj taranır; parse edilenler SIGNAL_EXT_TELEGRAM olarak loglanır.
- Canlı Akış: Keşfedilen chat’lerde yeni mesajlar dinlenir ve loglanır.
- Checkpoint: `telegram/checkpoints.json` ile kalınan yer saklanır.

## Log Formatı
`backend/data/logs/YYYY-MM-DD/events-XX.jsonl` dosyalarına şu şemada yazar:
```
{
  "ts": "2025-09-16T12:34:56Z",
  "event_type": "SIGNAL_EXT_TELEGRAM",
  "symbol": "ETHUSDT",
  "payload": {
    "chat_id": -100123,
    "chat_title": "Crypto Alpha",
    "message_id": 456,
    "text": "ETH/USDT LONG entry 4600 sl 4550 tp 4650",
    "signal": {"symbol":"ETHUSDT","side":"LONG","entry":4600,"sl":4550,"tp":4650,"confidence":0.8},
    "fp": "<trace_id>",
    "source": "live|backfill"
  },
  "trace_id": null
}
```

## Backend API
- GET /telegram/signals?limit=50 — Son sinyaller
  - Dönen alanlar: ts, chat_title, symbol, side, confidence, trace_id

## MiniApp
- Panel otomatik olarak `/telegram/signals`’ı çekerek “Telegram Signals” tablosunda gösterir.
- Trace butonu, trace_id ile `/events?trace_id=` görünümünü açar.

## Reputation & Ensemble Bias
Telegram sinyalleri karar motorunda “bias” olarak kullanılabilir.

- Reputation (itibar): Her chat için rolling performans skoru. Örnek yaklaşım:
  - `reputation = 2*hit_rate + 0.5*avg_rr - penalty(spam)`; yarı ömür (`reputation_half_life_days`) ile ağırlıklandır.
  - Kaynak: `SIGNAL_EXT_TELEGRAM` → gerçekleşen trade sonuçları (PnL, RR, MFE/MAE) ile eşle.
  - Önerilen dosya: `backend/src/reports/telegram_reputation.py` (DuckDB/Polars).

- Ensemble Bias: `backend/src/features/telegram.py` içindeki `telegram_bias(model_direction, signal_direction, group_reputation, max_bias)` ile uygulanır.
  - Uyum (model == sinyal): +bias (0.05–0.15 arası), Çelişki: −bias.
  - Bias, grup itibar skoru ile çarpılarak ölçeklenir ve `signals/hybrid.py` toplam skora eklenir.

- Risk kapısı: Aşağıdaki koşullar sağlanırsa trade tetiklenir, aksi halde sadece feature olarak kullanılır:
  1) Chat whitelist’te ise,
  2) Reputation ≥ eşik (`configs/telegram.yaml` → `scoring.min_group_reputation`),
  3) Model/trend ile yön uyumu varsa.

Uygulama adımları (özet):
1) `backend/src/reports/telegram_reputation.py`: DuckDB ile `SIGNAL_EXT_TELEGRAM` → realized sonuç eşleşmesi ve skor.
2) `backend/src/features/telegram.py`: mevcut `telegram_bias` fonksiyonu reputation’ı girdi olarak kabul ediyor; `hybrid.py`’a entegre edin.
3) `backend/src/signals/hybrid.py`: `p_long = soft_vote(trend, ml, news_bias, telegram_bias)` şeklinde bias ekleyin.

## Güvenlik
- Yalnızca üye olduğun chat’leri oku. Özel gruplarda yazılı izin gerekebilir.
- `telegram/sessions/` ve `telegram/checkpoints.json` repo dışında ve şifreli diskte tutulmalıdır. `.gitignore`’a eklenmiştir.
