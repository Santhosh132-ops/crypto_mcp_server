# 💰 Cryptocurrency Market Data Protocol (MCP) Server



A robust, asynchronous, and fully tested server that provides **real-time** and **historical** cryptocurrency market data.  
The system is designed following modern Market Data Protocol (MCP) principles: **caching**, **clear data contracts**, and **high reliability**.



## 📘 Introduction

This project implements a high-performance cryptocurrency market data server using **FastAPI** and **CCXT**, delivering a stable API for real-time and historical price data.  
It emphasizes:

- **Efficiency** (async ASGI stack)  
- **Abstraction** (CCXT unified API)  
- **Reliability** (caching + strict validation)  
- **Test coverage** (7 automated tests)  

---

## 🏛 Architectural Overview

### Core Strategy

A professional market data API requires reliability, low latency, and rate-limit awareness.  
This system achieves that using:

- **Asynchronous FastAPI** for high throughput  
- **Pydantic** for enforcement of strict and predictable data contracts  
- **CCXT** for safe and unified access to exchange data  
- **5-second TTL caching** to reduce API load and avoid hitting rate limits  

---

## 🔧 Key Components

| Component | Technology | Rationale |
|----------|------------|-----------|
| **Server Framework** | FastAPI | Fast, async-ready, auto validation + docs |
| **Market Data Source** | CCXT | Unified exchange API abstraction |
| **Caching** | Custom `DataCacher` with TTL | Prevents excessive external API calls |
| **Routing** | `{symbol:path}` | Supports symbols like `BTC/USDT` |







# 2. Setup and Validation (Evaluator’s Guide)


-  Clone the repository  
-  Install dependencies:

```bash
pip install -r requirements.txt
```



 ✅ Running Tests

The project includes a comprehensive test suite   (test_crypto_data.py) covering:

- Real-time data retrieval

 - Historical OHLCV retrieval

 - Cache refresh behavior

 - Invalid symbol error handling

 - API stability


 #  Run tests:
 ```bash
 pytest
```
# Expected output:
```bash
7 passed
```
# API Usage Guide:
Start the Server
```bash
uvicorn crypto_data_server:app --reload
```
#  Interactive Documentation
Open Swagger UI:
```bash
http://127.0.0.1:8000/docs
```
# Endpoint Examples
| Feature                      | Example URL                                                      | Description                         |
| ---------------------------- | ---------------------------------------------------------------- | ----------------------------------- |
| **Health Check**             | `http://127.0.0.1:8000/`                                         | Confirms API + Binance connectivity |
| **Real-Time BTC/USDT Price** | `http://127.0.0.1:8000/realtime/BTC/USDT`                        | Returns current price (cached 5s)   |
| **Real-Time ETH/USDT Price** | `http://127.0.0.1:8000/realtime/ETH/USDT`                        | Works for any valid trading pair    |
| **Historical OHLCV**         | `http://127.0.0.1:8000/historical/SOL/USDT?timeframe=4h&limit=5` | Fetches 5 candlestick entries       |
| **Invalid Pair Test**        | `http://127.0.0.1:8000/realtime/NONEXISTENT/PAIR`                | Returns 404 with clean JSON error   |


# Caching & Price Discrepancy Explanation
You may observe slight price differences vs. Binance's website.

| Platform            | Data Source        | Behavior                         |
| ------------------- | ------------------ | -------------------------------- |
| **Binance Website** | WebSocket stream   | Instant, real-time price updates |
| **This API**        | REST API + caching | 5-second TTL for reliability     |

This difference confirms that the caching layer is functioning correctly — a deliberate design choice to prevent rate limiting and ensure stability


# ⭐ Features

 - ⚡ Async FastAPI backend

 - 🔄 5-second TTL caching

 - 🔌 CCXT-powered unified exchange abstraction

 - 🧪 Automated 7-test suite

 - 🛡 Clean structured error handling

 - 🔗 Supports symbols containing / (e.g., BTC/USDT)

 - 📘 Automatic Swagger documentation


 # 🐞 Troubleshooting
 | Issue                    | Explanation / Fix                                 |
| ------------------------ | ------------------------------------------------- |
| **Price seems outdated** | Cache TTL still active (wait 5 seconds).          |
| **404 for trading pair** | Symbol may not exist on Binance.                  |
| **Tests failing**        | Ensure stable internet (CCXT fetches live data).  |
| **Server doesn't start** | Use correct module path: `crypto_data_server:app` |


