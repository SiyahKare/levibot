# Security Policy

## Supported Versions
We support the latest **minor** release line (e.g., v1.x). For older lines, only critical fixes are considered.

## Reporting a Vulnerability
- Email: security@siyahkare.dev (veya GitHub Security Advisory)
- Tercih: GitHub → *Security* → *Advisories* → *Report a vulnerability*
- Lütfen şunları ekleyin: etkilenen versiyon/tag, PoC, etki (CIA), CVSS tahmini.

**SLA hedefleri**
- İlk yanıt: 2 iş günü
- İlk değerlendirme/tekrar üretim: 5 iş günü
- Fix & release hedefi: 14 iş günü (kritik), 30 iş günü (yüksek)

## Scope
- API (FastAPI), Panel (React), Ops (Docker/Nginx), ML boru hattı, Redis RL, S3 Archiver.
- Dış bağımlılıklar (0x/Reservoir/Telethon) "best-effort".

## Security Hardening (özet)
- API key + Redis rate limit
- PII masking
- Liveness/Readiness probes
- Build info metric (gözlenebilirlik)
- S3 archiver için least-privilege IAM prensibi

## Responsible Disclosure
Lütfen halka açık istismar paylaşmadan önce gizli olarak raporlayın. Teşekkürler! 🙏
