# SECUROXI AI — Network Security Architecture Specification

**Engine Version**: `0.5.0-network-architecture`  
**Classification**: **`NETWORK SEGMENTATION & INGRESS SPECIFICATION`**  
**Reverse Proxy Target**: **`Nginx Ingress (docker/nginx/nginx.conf)`**  
**Date**: `2026-08-14`

---

## 1. Enterprise Network Segmentation Topology

```
                               [PUBLIC INTERNET]
                                       │
                         (HTTPS:443 / HTTP:80 Redirect)
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │   SECUROXI REVERSE PROXY / INGRESS     │
                  │   (Nginx Ingress: docker/nginx/conf)    │
                  │   - TLS 1.3 / 1.2 Termination           │
                  │   - Security Headers (HSTS, CSP, XFO)   │
                  │   - Rate Limiting & Max Upload Capping  │
                  └────────────────────┬────────────────────┘
                                       │
                               (Internal Bridge)
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
┌──────────────┐              ┌─────────────────┐             ┌────────────────┐
│ SECUROXI API │              │   POSTGRESQL    │             │  REDIS BROKER  │
│ (Internal)   │─────────────►│ (Internal Only) │────────────►│ (Internal Only)│
│ Port 8000    │              │ Port 5432       │             │ Port 6379      │
└──────────────┘              └─────────────────┘             └────────────────┘
```

---

## 2. Public vs. Internal Service Classification

| Service | Boundary | Public Ports | Internal Network | Firewall Policy |
| :--- | :--- | :--- | :--- | :--- |
| **`securoxi-proxy` (Nginx)** | **PUBLIC** | `80`, `443` | `securoxi-bridge` | ALLOW 80/443 Inbound |
| **`securoxi-api` (FastAPI)** | **INTERNAL** | None | `securoxi-bridge:8000` | Block External Access |
| **`securoxi-postgres`** | **DATABASE-ONLY** | None | `securoxi-bridge:5432` | Block External Access |
| **`securoxi-redis`** | **BROKER-ONLY** | None | `securoxi-bridge:6379` | Block External Access |

---

## 3. Status Decision Choice

# **`PASS`**
