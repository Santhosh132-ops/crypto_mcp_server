import pytest
from crypto_data_server import app, CACHE, EXCHANGE_ID, API_KEY
from fastapi.testclient import TestClient

# Constants for testing
VALID_SYMBOL = "BTC/USDT"
INVALID_SYMBOL = "XXX/YYY" 
VALID_TIMEFRAME = "1h"
# Headers required for authentication
AUTH_HEADERS = {"X-API-Key": API_KEY} 
INVALID_HEADERS = {"X-API-Key": "WRONG_KEY"}
UNAUTHENTICATED_HEADERS = {}


# -----------------
# PYTEST FIXTURES (Setup)
# -----------------

@pytest.fixture(scope="module")
def client():
    """
    Provides the standard synchronous FastAPI TestClient, which is used
    to test the async API endpoints reliably.
    """
    CACHE.clear()
    with TestClient(app) as c:
        yield c

# -----------------
# 1. STATUS & SECURITY TESTS
# -----------------

def test_system_status_success(client):
    """Test the root endpoint for system status (which requires no key)."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["exchange_id"] == EXCHANGE_ID

def test_security_access_denied(client):
    """TEST SECURITY: Ensures a protected route returns 403 when no key is provided."""
    response = client.get(f"/realtime/{VALID_SYMBOL}", headers=UNAUTHENTICATED_HEADERS)
    assert response.status_code == 403
    assert "Invalid API Key" in response.json()["detail"]

def test_security_invalid_key(client):
    """TEST SECURITY: Ensures a protected route returns 403 when a wrong key is provided."""
    response = client.get(f"/realtime/{VALID_SYMBOL}", headers=INVALID_HEADERS)
    assert response.status_code == 403
    assert "Invalid API Key" in response.json()["detail"]


# -----------------
# 2. REAL-TIME DATA (TICKER) TESTS
# -----------------

def test_get_realtime_price_success(client):
    """Test fetching a valid symbol price with the correct key."""
    CACHE.clear() 
    # NOTE: Added headers=AUTH_HEADERS
    response = client.get(f"/realtime/{VALID_SYMBOL}", headers=AUTH_HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == VALID_SYMBOL
    assert isinstance(data["price"], (float, int))

def test_get_realtime_price_cache_hit(client):
    """Test that the cache is used on the second call (critical test)."""
    CACHE.clear()
    
    # 1. First call (Cache Miss) - populates the cache
    # NOTE: Added headers=AUTH_HEADERS
    response_miss = client.get(f"/realtime/{VALID_SYMBOL}", headers=AUTH_HEADERS)
    initial_price = response_miss.json()["price"]
    
    # 2. Second call (Cache Hit) - retrieves from cache
    # NOTE: Added headers=AUTH_HEADERS
    response_hit = client.get(f"/realtime/{VALID_SYMBOL}", headers=AUTH_HEADERS)
    
    # Data must be identical, proving it came from the cache
    assert response_hit.json()["price"] == initial_price

def test_get_realtime_price_invalid_symbol(client):
    """Test handling of a non-existent symbol (404 Error) with the correct key."""
    # NOTE: Added headers=AUTH_HEADERS
    response = client.get(f"/realtime/{INVALID_SYMBOL}", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert "not found on binance" in response.json()["detail"]

# -----------------
# 3. HISTORICAL DATA (OHLCV) TESTS
# -----------------

def test_get_historical_data_success(client):
    """Test fetching historical data with the correct key."""
    CACHE.clear()
    limit = 5 
    # NOTE: Added headers=AUTH_HEADERS
    response = client.get(f"/historical/{VALID_SYMBOL}?timeframe={VALID_TIMEFRAME}&limit={limit}", headers=AUTH_HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["symbol"] == VALID_SYMBOL
    assert data["count"] <= limit
    assert len(data["data"]) > 0

def test_get_historical_data_invalid_timeframe(client):
    """Test handling of an unsupported timeframe (400 Error) with the correct key."""
    invalid_tf = "1w00" 
    # NOTE: Added headers=AUTH_HEADERS
    response = client.get(f"/historical/{VALID_SYMBOL}?timeframe={invalid_tf}", headers=AUTH_HEADERS)
    assert response.status_code == 400
    assert f"Invalid timeframe: '{invalid_tf}'" in response.json()["detail"]

def test_historical_data_cache_integration(client):
    """Test historical cache is used for identical queries with the correct key."""
    CACHE.clear()
    
    # Query 1 (Miss)
    query_params = {"timeframe": "1m", "limit": 2}
    # NOTE: Added headers=AUTH_HEADERS
    response1 = client.get(f"/historical/{VALID_SYMBOL}", params=query_params, headers=AUTH_HEADERS)
    data1 = response1.json()
    
    # 2. Query 2 (Hit)
    # NOTE: Added headers=AUTH_HEADERS
    response2 = client.get(f"/historical/{VALID_SYMBOL}", params=query_params, headers=AUTH_HEADERS)
    data2 = response2.json()

    # The data content must be exactly the same
    assert data1["data"] == data2["data"]