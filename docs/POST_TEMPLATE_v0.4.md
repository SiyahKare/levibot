# LeviBot v0.4 (miniface) — AI → Risk → On‑Chain (Base testnet)

5 dakikada ayağa kalkıyor: `/signals/run`, `/exec/dry-run`, `/exec/submit` + `/metrics`.

- Repo + demo mp4: <link>
- Not: Testnet; gerçek para yok. Safe/4337 module sonraki sürümde.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # RPC_BASE_SEPOLIA, SAFE_ADDRESS, SESSION_PK doldur
make api_miniface     # http://localhost:8000/docs
```

Öne çıkanlar:

- Minimal API yüzeyi (3 endpoint)
- Risk motoru (allowed_pairs + max_position_usd)
- Prometheus telemetry (`/metrics`)
- Base Sepolia submit (env yoksa `0xMOCK`)

Roadmap (kısa):

- Safe Module + allowlist (gerçek calldata builder)
- `pkgs/risk` ve `pkgs/exchange` paketleri
- OpenAPI client (panel & test)
