# 🛡 Self-Improving AI Harness — Mirrors API

Every AI agent operating in this workspace must strictly follow the 5-step closed-loop lifecycle:
spec ➔ execution ➔ verification ➔ retro ➔ improvement

---

## 1. The 5-Step Invariant Cycle
1. **SPEC:** Plan endpoints and data contracts before modifying FastAPI services.
2. **EXECUTION:** Minimal, robust asynchronous code.
3. **VERIFICATION:**
   - Rate Limiter: verify Sliding Window limits and dynamic Retry-After.
   - Security: verify no `.env*` or `token.json` files are tracked in git.
4. **RETRO:** Analyze any HTTP 429, timeout, or memory leak.
5. **IMPROVEMENT:** Save learnings into Active Invariants below.

---

## 2. Active Invariants
- [2026-10-03] Rate Limiting: Always use SlidingWindowRateLimiter with `_cleanup_stale_keys` to prevent memory leaks.
- [2026-10-03] Secret Isolation: `.env.save`, `token.json`, and `.env` must NEVER be tracked in git index.
- [2026-10-03] Exempt Endpoints: `/health`, `/metrics`, and `/docs` must bypass rate limiting.
