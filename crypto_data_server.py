import ccxt.async_support as ccxt
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Import the caching utility
from data_cacher import CACHE

# --- Pydantic Models for Data Validation and Response Structure ---

class TickerResponse(BaseModel):
    """Schema for real-time price response."""
    symbol: str = Field(..., example="BTC/USDT")
    price: float = Field(..., example=65000.50)
    timestamp_ms: int = Field(..., description="Timestamp of the exchange's data in milliseconds.")
    source_exchange: str = Field(..., example="binance")

class OHLCVDataPoint(BaseModel):
    """Schema for a single OHLCV candlestick."""
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class HistoricalResponse(BaseModel):
    """Schema for historical data query results."""
    symbol: str
    timeframe: str
    data: List[OHLCVDataPoint]
    source_exchange: str = Field(..., example="binance")
    count: int = Field(..., description="Number of candles returned.")


# --- Exchange and Application Initialization ---

EXCHANGE_ID = 'binance'

try:
    ExchangeClass = getattr(ccxt, EXCHANGE_ID)
    EXCHANGE = ExchangeClass({
        'enableRateLimit': True,
        'rateLimit': 500,
        'options': {'defaultType': 'spot'},
    })
except AttributeError:
    raise RuntimeError(f"Could not initialize CCXT exchange: {EXCHANGE_ID}")


app = FastAPI(
    title="Crypto Market Data Protocol (MCP) Server",
    description="A robust, cached FastAPI server to fetch real-time and historical market data using CCXT.",
    version="1.0.0",
)


# --- Dependency Injectors and Utility Functions ---

async def get_exchange_instance():
    """Dependency that yields the global CCXT exchange instance."""
    return EXCHANGE

async def get_exchange_markets(exchange: ccxt.Exchange = Depends(get_exchange_instance)):
    """Loads markets and caches the result for quick symbol validation."""
    cache_key = f"{exchange.id}_markets"
    markets = CACHE.get(cache_key) 
    
    if not markets:
        try:
            markets = await exchange.load_markets()
            # Cache market list for 1 hour to reduce startup lag
            CACHE.set(cache_key, markets, ttl=(60 * 60)) 
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=f"Failed to load exchange markets. CCXT Error: {e}"
            )
            
    return markets

def validate_symbol(symbol: str, markets: Dict[str, Any]):
    """Checks if the symbol is valid and available on the exchange."""
    # Standardize symbol to uppercase for the exchange API
    symbol = symbol.upper()
    if symbol not in markets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{symbol}' not found on {EXCHANGE_ID}. Example: BTC/USDT"
        )
    return symbol


# --- API Endpoints ---

@app.get("/", status_code=status.HTTP_200_OK)
async def system_status(exchange: ccxt.Exchange = Depends(get_exchange_instance)):
    """
    Returns the server and exchange status for a system health check.
    """
    try:
        await exchange.fetch_status()
        server_time = await exchange.fetch_time()
        
        return {
            "status": "online",
            "server_time_ms": int(time.time() * 1000),
            "exchange_id": EXCHANGE_ID,
            "exchange_status": "connected",
            "exchange_time_ms": server_time,
            "cache_ttl_seconds": CACHE.default_ttl_ms / 1000,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Exchange connection failed: {e.args[0]}"
        )


@app.get("/realtime/{symbol:path}", response_model=TickerResponse, status_code=status.HTTP_200_OK)
async def get_realtime_price(
    symbol: str, 
    exchange: ccxt.Exchange = Depends(get_exchange_instance),
    markets: Dict[str, Any] = Depends(get_exchange_markets)
):
    """
    Fetches the latest real-time ticker price, utilizing the 5-second TTL cache.
    """
    symbol = validate_symbol(symbol, markets)
    cache_key = f"ticker:{symbol}"
    
    # Check cache for recent data
    cached_data = CACHE.get(cache_key)
    if cached_data:
        return cached_data

    # If cache miss, fetch data from the exchange
    try:
        ticker = await exchange.fetch_ticker(symbol)
        
        response_data = TickerResponse(
            symbol=ticker['symbol'],
            price=ticker['last'], 
            timestamp_ms=ticker['timestamp'],
            source_exchange=EXCHANGE_ID
        )
        
        # Store in cache with the default 5s TTL
        CACHE.set(cache_key, response_data)
        
        return response_data

    except ccxt.ExchangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Exchange Error for {symbol}: {e.args[0]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Internal Server Error: {e}"
        )


@app.get("/historical/{symbol:path}", response_model=HistoricalResponse, status_code=status.HTTP_200_OK)
async def get_historical_data(
    symbol: str,
    timeframe: str = '1h', 
    limit: int = 100, 
    exchange: ccxt.Exchange = Depends(get_exchange_instance),
    markets: Dict[str, Any] = Depends(get_exchange_markets)
):
    """
    Fetches historical OHLCV data for backtesting and analysis.
    """
    symbol = validate_symbol(symbol, markets)

    if timeframe not in exchange.timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe: '{timeframe}'. Supported: {', '.join(exchange.timeframes.keys())}"
        )

    # Key includes all query parameters for uniqueness
    cache_key = f"ohlcv:{symbol}:{timeframe}:{limit}"
    
    # Check cache for recent data
    cached_data = CACHE.get(cache_key)
    if cached_data:
        return cached_data

    # If cache miss, fetch data from the exchange
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        if not ohlcv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No historical data found for {symbol} at timeframe {timeframe}."
            )
            
        data_points = [
            OHLCVDataPoint(
                timestamp_ms=point[0],
                open=point[1],
                high=point[2],
                low=point[3],
                close=point[4],
                volume=point[5]
            ) for point in ohlcv
        ]

        response_data = HistoricalResponse(
            symbol=symbol,
            timeframe=timeframe,
            data=data_points,
            source_exchange=EXCHANGE_ID,
            count=len(data_points)
        )
        
        # Store data with a 60 minute TTL, as historical data is static
        CACHE.set(cache_key, response_data, ttl=(60 * 60)) 

        return response_data

    except ccxt.ExchangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Exchange Error for {symbol}: {e.args[0]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"A network or processing error occurred: {e}"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Close CCXT connection cleanly on server shutdown."""
    await EXCHANGE.close()
    print(f"\nCCXT connection to {EXCHANGE_ID} closed.")