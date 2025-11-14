# 💰 Cryptocurrency Market Data Protocol (MCP) Server


This project implements a robust, structured, and fully tested server to provide real-time and historical cryptocurrency market data. It adheres to the principles of a modern MCP by emphasizing **caching, clear data contracts, and high reliability**.

---

## 1. Architectural Approach and Design

The server is built to adhere to industry best practices, prioritizing stability and efficient resource usage ("zero cost").

### Key Components:

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Server Framework** | **FastAPI** | High performance (ASGI), automatic data validation via Pydantic, and self-documenting API (Swagger UI). |
| **Data Source** | **CCXT** | Provides a **Unified API** to abstract exchange complexity (using **Binance** for public market data). |
| **Caching/Rate Limiting** | **Custom `DataCacher` (TTL)** | Prevents excessive calls to the external API. Real-time data is cached for **5 seconds** for high availability. |
| **Routing** | **`:path` Converter** | Used on dynamic routes (`/realtime/{symbol:path}`) to correctly handle symbols containing slashes (e.g., `BTC/USDT`), resolving a common routing bug. |

---

## 2. Setup and Validation (The Evaluator's Guide)

Follow these steps to clone the repository, set up the environment, and validate all functionality.

### A. Installation

1.  **Clone the repository.**
2.  **Install Dependencies:** All required packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### B. Validation: Running the Tests (Proof of Robustness)

The project includes a comprehensive test suite (`test_crypto_data.py`) to prove its reliability and validate all core features, including **caching logic** and **error handling**.

Run the following command in the terminal:

```bash
pytest