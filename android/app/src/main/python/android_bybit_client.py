"""Small public-only Bybit V5 client for Android.

Implements the subset of the CCXT interface used by Atlas market analysis.
No authenticated trading endpoints are exposed.
"""
import time
import requests

_BASE = "https://api.bybit.com"
_INTERVALS = {"1m":"1","3m":"3","5m":"5","15m":"15","30m":"30","1h":"60","2h":"120","4h":"240","6h":"360","12h":"720","1d":"D","1w":"W"}

class AndroidBybitPublicClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Atlas-Android/1.0"})
        self._markets = None

    def _get(self, path, params=None):
        response = self.session.get(_BASE + path, params=params or {}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if payload.get("retCode", 0) != 0:
            raise RuntimeError("Bybit API: " + str(payload.get("retMsg", "unknown error")))
        return payload.get("result") or {}

    @staticmethod
    def _symbol(symbol):
        return str(symbol).upper().replace("/", "").replace(":USDT", "")

    def milliseconds(self):
        return int(time.time() * 1000)

    def parse_timeframe(self, timeframe):
        seconds = {"1m":60,"3m":180,"5m":300,"15m":900,"30m":1800,"1h":3600,"2h":7200,"4h":14400,"6h":21600,"12h":43200,"1d":86400,"1w":604800}
        return seconds[timeframe]

    def load_markets(self):
        if self._markets is not None:
            return self._markets
        markets = {}
        cursor = None
        for _ in range(10):
            params = {"category":"linear", "limit":1000}
            if cursor:
                params["cursor"] = cursor
            result = self._get("/v5/market/instruments-info", params)
            for item in result.get("list", []):
                if item.get("status") != "Trading" or item.get("quoteCoin") != "USDT":
                    continue
                base = item.get("baseCoin")
                if base:
                    symbol = base + "/USDT:USDT"
                    markets[symbol] = {"symbol":symbol, "base":base, "quote":"USDT", "active":True}
            cursor = result.get("nextPageCursor")
            if not cursor:
                break
        self._markets = markets
        return markets

    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        interval = _INTERVALS[timeframe]
        result = self._get("/v5/market/kline", {"category":"linear","symbol":self._symbol(symbol),"interval":interval,"limit":min(int(limit),1000)})
        rows = []
        for item in reversed(result.get("list", [])):
            rows.append([int(item[0]), float(item[1]), float(item[2]), float(item[3]), float(item[4]), float(item[5])])
        return rows

    def fetch_order_book(self, symbol, limit=50):
        result = self._get("/v5/market/orderbook", {"category":"linear","symbol":self._symbol(symbol),"limit":min(int(limit),200)})
        return {"bids":[[float(x[0]),float(x[1])] for x in result.get("b",[])],
                "asks":[[float(x[0]),float(x[1])] for x in result.get("a",[])],
                "timestamp":int(result.get("ts") or self.milliseconds())}

    def fetch_trades(self, symbol, limit=200):
        result = self._get("/v5/market/recent-trade", {"category":"linear","symbol":self._symbol(symbol),"limit":min(int(limit),1000)})
        trades=[]
        for x in result.get("list",[]):
            price=float(x["price"]); amount=float(x["size"])
            trades.append({"id":x.get("execId"),"timestamp":int(x["time"]),"symbol":symbol,
                           "side":"buy" if x.get("side")=="Buy" else "sell","price":price,
                           "amount":amount,"cost":price*amount})
        return trades

    def fetch_open_interest_history(self, symbol, timeframe="1h", limit=100):
        result=self._get("/v5/market/open-interest", {"category":"linear","symbol":self._symbol(symbol),
                       "intervalTime":timeframe,"limit":min(int(limit),200)})
        return [{"timestamp":int(x["timestamp"]),"openInterestAmount":float(x["openInterest"])} for x in reversed(result.get("list",[]))]

    def fetch_open_interest(self, symbol):
        records=self.fetch_open_interest_history(symbol,"1h",1)
        return records[-1] if records else {}

    def fetch_funding_rate_history(self, symbol, limit=100):
        result=self._get("/v5/market/funding/history", {"category":"linear","symbol":self._symbol(symbol),"limit":min(int(limit),200)})
        return [{"timestamp":int(x["fundingRateTimestamp"]),"fundingRate":float(x["fundingRate"])} for x in reversed(result.get("list",[]))]

    def fetch_funding_rate(self, symbol):
        result=self._get("/v5/market/tickers", {"category":"linear","symbol":self._symbol(symbol)})
        rows=result.get("list",[])
        return {"fundingRate":float(rows[0]["fundingRate"])} if rows else {}

    def fetch_ticker(self, symbol):
        result=self._get("/v5/market/tickers", {"category":"linear","symbol":self._symbol(symbol)})
        rows=result.get("list",[])
        if not rows:
            return {}
        row=rows[0]
        return {"last":float(row["lastPrice"]),"timestamp":int(result.get("ts") or self.milliseconds())}
