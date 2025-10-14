# 🔐 Security Checklist — LeviBot Production

**Status:** In Progress  
**Last Updated:** 2025-10-11  
**Next Review:** 2025-10-18

---

## ✅ Completed

### Authentication & Authorization

- [x] **Admin Key Rotated** — New 64-char key generated

  - Old key: `mx0vglSTklRnK3TCDu` (COMPROMISED - shown in chat)
  - New key: `d4f35619c7fdda3977854335960f5e2738ecdf64fe67901c09a709ca643fdccf`
  - Location: `.env.docker` (not in git)
  - **Action:** Update panel login with new key

- [x] **IP Allowlist** — Restricted to localhost

  - Current: `127.0.0.1, ::1`
  - **TODO:** Add office/home IPs in production

- [x] **Cookie Auth** — HttpOnly cookies enabled
  - SameSite: Lax
  - Secure flag: TODO (enable with HTTPS)

### Secrets Management

- [x] **Environment Variables** — Secrets in `.env.docker`
- [x] **Git Ignore** — `.env*` files ignored
- [ ] **Secrets Scanner** — TODO: Add pre-commit hook
  - Recommended: `detect-secrets` or `trufflehog`

### API Security

- [x] **Admin Endpoints Protected** — `require_admin` dependency
- [x] **Rate Limiting** — Redis-based distributed rate limiting
- [x] **CORS** — Configured for specific origins
- [ ] **HTTPS Only** — TODO: Production reverse proxy
  - Example config: `ops/nginx-https.conf.example`

### Data Protection

- [x] **Database Backup** — Daily at 03:10

  - Script: `scripts/db_backup.sh`
  - Retention: 14 days
  - Location: `/Users/onur/levibot/backups/db/`

- [x] **Config Snapshots** — Every 30 minutes

  - Auto-commit to git
  - Location: `ops/config-snapshots/`

- [x] **Log Rotation** — Setup script ready
  - Script: `scripts/setup_logrotate.sh`
  - Retention: 14-90 days depending on log type

### Monitoring & Alerts

- [x] **Telegram Alerts** — Critical events
- [x] **Cron Health Checks** — Every 5 minutes
- [x] **Audit Logging** — All admin actions logged
  - Location: `ops/audit.log`

---

## 🔴 Critical TODOs (Before Production)

### 1. HTTPS Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

**OR** use Traefik/Caddy for automatic Let's Encrypt

### 2. Update IP Allowlist

```bash
# Edit .env.docker
IP_ALLOWLIST=127.0.0.1,::1,YOUR_OFFICE_IP,PROD_INGRESS_IP

# Restart API
docker compose restart api
```

### 3. Enable Secure Cookies

```bash
# In .env.docker
SECURE_COOKIES=true  # Only with HTTPS

# Restart API
docker compose restart api
```

### 4. Secrets Scanner

```bash
# Install pre-commit
pip install pre-commit

# Add .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF

# Initialize
pre-commit install
detect-secrets scan > .secrets.baseline
```

---

## ⚠️ Medium Priority

### Password Policy

- [ ] Enforce minimum key length (32+ chars)
- [ ] Key rotation schedule (every 90 days)
- [ ] Document key rotation procedure

### Network Security

- [ ] VPN/private network for admin access
- [ ] Firewall rules (block non-essential ports)
- [ ] DDoS protection (Cloudflare/AWS Shield)

### Database Security

- [ ] Encrypted backups
- [ ] Off-site backup storage (S3/GCS)
- [ ] Database access audit log
- [ ] Least privilege principle for DB users

### Application Security

- [ ] Input validation (all API endpoints)
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS protection (already enabled in headers)
- [ ] CSRF protection (consider for state-changing ops)

---

## 📊 Security Monitoring

### Daily Checks

```bash
# Failed login attempts
grep "admin_login_failed" ops/audit.log | tail -20

# Suspicious IP activity
grep "403\|401" /var/log/nginx/levibot_access.log | tail -50

# Kill switch events
grep "kill\|unkill" ops/audit.log | tail -10
```

### Weekly Reviews

- Review audit logs for anomalies
- Check backup integrity
- Verify cron jobs running
- Review Telegram alert history

### Monthly Tasks

- Rotate admin keys
- Update dependencies (`pip install --upgrade`, `npm update`)
- Security patch review
- Penetration testing (if applicable)

---

## 🧯 Incident Response

### If Admin Key Compromised

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -hex 32)

# 2. Update .env.docker
sed -i.bak "s/^ADMIN_KEY=.*/ADMIN_KEY=${NEW_KEY}/" .env.docker

# 3. Restart API
docker compose restart api

# 4. Update all clients/scripts
# 5. Audit recent admin actions
grep "admin" ops/audit.log | tail -100

# 6. Check for unauthorized changes
git log -p --since="1 day ago" configs/
```

### If Unauthorized Access Detected

```bash
# 1. Activate kill switch
bash scripts/emergency_controls.sh kill

# 2. Review audit logs
tail -200 ops/audit.log

# 3. Check recent trades
curl -s http://localhost:8000/paper/trades?limit=50 | jq

# 4. Rotate all keys
# 5. Add attacker IP to blocklist
# 6. Investigate entry point
```

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Nginx Security Hardening](https://www.cyberciti.biz/tips/linux-unix-bsd-nginx-webserver-security.html)

---

## ✅ Compliance (If Applicable)

- [ ] GDPR (if processing EU user data)
- [ ] SOC 2 (if enterprise customers)
- [ ] ISO 27001 (information security)
- [ ] PCI DSS (if handling payment cards)

---

**Last Security Audit:** 2025-10-11  
**Next Audit:** 2025-10-18  
**Responsible:** Security Team / DevSecOps

**Notes:**

- Admin key rotated due to exposure in development chat
- Production HTTPS setup pending
- All critical security measures in place for staging
- Follow this checklist before public production launch
