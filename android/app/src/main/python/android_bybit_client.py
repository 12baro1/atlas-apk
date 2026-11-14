"""Android-only public Bybit V5 adapter implementing the subset of CCXT used by Atlas.

This module deliberately exposes public market-data methods only. It does not
support authenticated endpoints or order placement.
"""
import time
import requests


class AndroidBybitPublicClient:
    BASE_URL = "https://api.bybit.com"

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Atlas-Android/1.0"})
        self.markets = {}

    @staticmethod
    def _symbol(symbol):
        # CCXT linear perpetual format: BTC/USDT:USDT -> BTCUSDT
        return str(symbol).split(":")[0].replace("/", "").replace("-", "").upper()

    @staticmethod
    def parse_timeframe(timeframe):
        value = str(timeframe).strip().lower()
        units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
        if not value or value[-1] not in units:
            raise ValueError("Unsupported timeframe: " + value)
        return int(value[:-1]) * units[value[-1]]

    @staticmethod
    def milliseconds():
        return int(time.time() * 1000)

    def _get(self, path, params):
        response = self.session.get(
            self.BASE_URL + path, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("retCode") != 0:
            raise RuntimeError(
                "Bybit API error %s: %s" %
                (payload.get("retCode"), payload.get("retMsg"))
            )
        return payload.get("result") or {}

    def load_markets(self, reload=False):
        if not self.markets or reload:
            result = self._get(
                "/v5/market/instruments-info",
                {"category": "linear", "limit": 1000},
            )
            self.markets = {
                item.get("symbol"): item
                for item in result.get("list", [])
                if item.get("symbol")
            }
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=500, params=None):
        interval_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15",
            "30m": "30", "1h": "60", "2h": "120", "4h": "240",
            "6h": "360", "12h": "720", "1d": "D", "1w": "W",
        }
        interval = interval_map.get(str(timeframe))
        if interval is None:
            raise ValueError("Unsupported Bybit kline timeframe: " + str(timeframe))
        query = {
            "category": "linear",
            "symbol": self._symbol(symbol),
            "interval": interval,
            "limit": max(1, min(int(limit or 200), 1000)),
        }
        if since is not None:
            query["start"] = int(since)
        result = self._get("/v5/market/kline", query)
        rows = []
        for item in result.get("list", []):
            try:
                rows.append([
                    int(item[0]), float(item[1]), float(item[2]),
                    float(item[3]), float(item[4]), float(item[5])
                ])
            except (IndexError, TypeError, ValueError):
                continue
        rows.sort(key=lambda row: row[0])
        return rows

    def fetch_order_book(self, symbol, limit=50, params=None):
        result = self._get("/v5/market/orderbook", {
            "category": "linear",
            "symbol": self._symbol(symbol),
            "limit": max(1, min(int(limit or 50), 200)),
        })
        return {
            "symbol": symbol,
            "bids": [[float(p), float(q)] for p, q in result.get("b", [])],
            "asks": [[float(p), float(q)] for p, q in result.get("a", [])],
            "timestamp": int(result.get("ts") or self.milliseconds()),
            "datetime": None,
            "nonce": None,
            "info": result,
        }

    def fetch_trades(self, symbol, since=None, limit=200, params=None):
        result = self._get("/v5/market/recent-trade", {
            "category": "linear",
            "symbol": self._symbol(symbol),
            "limit": max(1, min(int(limit or 200), 1000)),
        })
        trades = []
        for item in result.get("list", []):
            try:
                timestamp = int(item["time"])
                if since is not None and timestamp < int(since):
                    continue
                trades.append({
                    "id": item.get("execId"),
                    "timestamp": timestamp,
                    "datetime": None,
                    "symbol": symbol,
                    "side": "buy" if item.get("side") == "Buy" else "sell",
                    "price": float(item["price"]),
                    "amount": float(item["size"]),
                    "cost": float(item["price"]) * float(item["size"]),
                    "info": item,
                })
            except (KeyError, TypeError, ValueError):
                continue
        trades.sort(key=lambda trade: trade["timestamp"])
        return trades

    def fetch_open_interest_history(self, symbol, timeframe="1h", since=None, limit=100, params=None):
        interval_map = {"5m": "5min", "15m": "15min", "30m": "30min",
                        "1h": "1h", "4h": "4h", "1d": "1d"}
        interval = interval_map.get(str(timeframe), "1h")
        result = self._get("/v5/market/open-interest", {
            "category": "linear",
            "symbol": self._symbol(symbol),
            "intervalTime": interval,
            "limit": max(1, min(int(limit or 100), 200)),
        })
        records = []
        for item in result.get("list", []):
            try:
                ts = int(item["timestamp"])
                if since is not None and ts < int(since):
                    continue
                records.append({
                    "timestamp": ts,
                    "openInterestAmount": float(item["openInterest"]),
                    "openInterestValue": None,
                    "info": item,
                })
            except (KeyError, TypeError, ValueError):
                continue
        records.sort(key=lambda item: item["timestamp"])
        return records

    def fetch_open_interest(self, symbol, params=None):
        records = self.fetch_open_interest_history(symbol, timeframe="5m", limit=1)
        if not records:
            return {}
        return records[-1]

    def fetch_funding_rate_history(self, symbol, since=None, limit=100, params=None):
        result = self._get("/v5/market/funding/history", {
            "category": "linear",
            "symbol": self._symbol(symbol),
            "limit": max(1, min(int(limit or 100), 200)),
        })
        records = []
        for item in result.get("list", []):
            try:
                ts = int(item["fundingRateTimestamp"])
                if since is not None and ts < int(since):
                    continue
                records.append({
                    "timestamp": ts,
                    "fundingRate": float(item["fundingRate"]),
                    "info": item,
                })
            except (KeyError, TypeError, ValueError):
                continue
        records.sort(key=lambda item: item["timestamp"])
        return records

    def fetch_funding_rate(self, symbol, params=None):
        result = self._get("/v5/market/tickers", {
            "category": "linear",
            "symbol": self._symbol(symbol),
        })
        items = result.get("list", [])
        if not items:
            return {}
        item = items[0]
        return {
            "symbol": symbol,
            "fundingRate": float(item["fundingRate"]) if item.get("fundingRate") is not None else None,
            "timestamp": int(result.get("ts") or self.milliseconds()),
            "info": item,
        }

    def fetch_ticker(self, symbol, params=None):
        result = self._get("/v5/market/tickers", {
            "category": "linear",
            "symbol": self._symbol(symbol),
        })
        items = result.get("list", [])
        if not items:
            return {}
        item = items[0]
        price = item.get("lastPrice")
        return {
            "symbol": symbol,
            "last": float(price) if price not in (None, "") else None,
            "timestamp": int(result.get("ts") or self.milliseconds()),
            "datetime": None,
            "info": item,
        }
