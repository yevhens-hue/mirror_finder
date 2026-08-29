# 🔍 Distributed Endpoint Discovery Engine

A robust networking utility built to automatically crawl, verify, and catalog distributed backup endpoints (mirrors) to guarantee 100% upstream availability for your primary applications.

## 📊 Overview
When running highly available systems, primary nodes can experience downtime or geographic blocking. This Python engine acts as an automated scout, dynamically mapping healthy alternative nodes:

- **Discovery Crawling:** Scans designated seed URLs or APIs to extract lists of alternative endpoints.
- **Health Checks:** Pings each discovered node to calculate response times and verify SSL/TLS handshakes.
- **Endpoint Cataloging:** Exports a clean, ranked list of healthy IP/URLs for downstream load balancers to use.

## 🛠 Tech Stack
- **Python 3.9+** (Fast networking and data manipulation)
- **Asyncio / Aiohttp** (Concurrent network requests)
- **Regex & DOM Parsing** (Extracting endpoints from messy HTML)

## 💡 Key Features

### 1. Concurrent Health Verification
Instead of pinging 1000 nodes sequentially (which takes hours), the engine utilizes Python's asynchronous capabilities to map the entire network mesh in seconds.
- ⚡ **LOW LATENCY:** Automatically ranks endpoints based on direct TCP ping response times.
- 🛡️ **STATUS CHECKS:** Drops nodes that return 4xx/5xx HTTP codes or mismatched SSL certificates.

### 2. Dynamic Update Pipeline
The engine produces a machine-readable JSON structure detailing the absolute fastest and healthiest routes for your frontend/backend systems to point to dynamically.

## 🚀 How to Run

1. **Install Connection Libraries:**
```bash
pip install -r requirements.txt
```

2. **Initiate Scan:**
```bash
python finder.py --concurrent 50 --export healthy_nodes.json
```


<!-- activity-sync: 2026-08-28 -->


<!-- activity-sync: 2026-08-28 -->


<!-- activity-sync: 2026-08-29 -->
