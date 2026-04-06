import requests
import datetime
import json

# ── Tool 1: Cafef ──────────────────────────────────────────────

def fetch_Cafef_stock(stock_name: str) -> str:
    """
    Fetch historical daily stock data from Cafef for a Vietnamese stock ticker.
    Input: stock ticker symbol (e.g. "VNM", "FPT", "VIC").
    Returns: JSON string with the latest 5 trading days (date, open, high, low, close, volume).
    """
    ticker = stock_name.upper()
    mock_data = [
        {"ticker": ticker, "date": "2025-06-02", "open": 90000, "high": 92000, "low": 89500, "close": 91000, "volume": 1200000},
        {"ticker": ticker, "date": "2025-06-03", "open": 91000, "high": 93000, "low": 90500, "close": 92500, "volume": 1350000},
        {"ticker": ticker, "date": "2025-06-04", "open": 92500, "high": 94000, "low": 91800, "close": 93200, "volume": 1100000},
        {"ticker": ticker, "date": "2025-06-05", "open": 93200, "high": 95000, "low": 92000, "close": 94500, "volume": 1500000},
        {"ticker": ticker, "date": "2025-06-06", "open": 94500, "high": 96000, "low": 93800, "close": 95500, "volume": 1400000},
    ]
    return json.dumps(mock_data, ensure_ascii=False)


# ── Tool 2: FireAnt ────────────────────────────────────────────

API_BEARER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkdYdExONzViZlZQakdvNERWdjV4QkRITHpnSSIsImtpZCI6IkdYdExONzViZlZQakdvNERWdjV4QkRITHpnSSJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmZpcmVhbnQudm4iLCJhdWQiOiJodHRwczovL2FjY291bnRzLmZpcmVhbnQudm4vcmVzb3VyY2VzIiwiZXhwIjoyMDQxMTcyNDIwLCJuYmYiOjE3NDExNzI0MjAsImNsaWVudF9pZCI6ImZpcmVhbnQudHJhZGVzdGF0aW9uIiwic2NvcGUiOlsib3BlbmlkIiwicHJvZmlsZSIsInJvbGVzIiwiZW1haWwiLCJhY2NvdW50cy1yZWFkIiwiYWNjb3VudHMtd3JpdGUiLCJvcmRlcnMtcmVhZCIsIm9yZGVycy13cml0ZSIsImNvbXBhbmllcy1yZWFkIiwiaW5kaXZpZHVhbHMtcmVhZCIsImZpbmFuY2UtcmVhZCIsInBvc3RzLXdyaXRlIiwicG9zdHMtcmVhZCIsInN5bWJvbHMtcmVhZCIsInVzZXItZGF0YS1yZWFkIiwidXNlci1kYXRhLXdyaXRlIiwidXNlcnMtcmVhZCIsInNlYXJjaCIsImFjYWRlbXktcmVhZCIsImFjYWRlbXktd3JpdGUiLCJibG9nLXJlYWQiLCJpbnZlc3RvcGVkaWEtcmVhZCJdLCJzdWIiOiI3ODY5YzE1ZS1kOTNlLTQ5ZGQtOWE5NC1iOTFmMDMyNjVhZmIiLCJhdXRoX3RpbWUiOjE3NDExNzI0MjAsImlkcCI6Ikdvb2dsZSIsIm5hbWUiOiJiZXN0eGFteGloaWV1QGdtYWlsLmNvbSIsInNlY3VyaXR5X3N0YW1wIjoiOGNlYmQwNDMtZTIyZi00N2Q0LThiMjAtN2RlZGNkMDJlY2M0IiwianRpIjoiOGY5MWMyMWQ0YWY4OGM3NGIzNGMxODVkZjQ2OTdiNjAiLCJhbXIiOlsiZXh0ZXJuYWwiXX0.vR1jAm3n1jaYcEiYgxKBgpVdM-IiclcuYMHNYO5eaS9jXOKPr-qtVnszQ-IjU6CUy65hz2aRXNHlOaRnD8z5kHJQuqgTS_2AxZwUD2hsnyqqtBtwluFt7BlZWEZH2FDgbRrg4h7qvmFI9iojFph8vWZr8NgGZed30T6lFGkAIzfEJeMraYIJabHK8Kmw-KX8C-kyYNHHDR0_CUrZ5BXoptlMJjv8XPLN3ROa8TFWIlU1e50S0V0fMxoc01jezLyWZXk0rn-x4fvnnCROMEeKY_TQr3cyfnyBiXLG7U_Qa9PnhqxoIrIU2L6fxcuaXvA-Cd5fWu24XO3H0dZqU6FK0A"
BASE_URL = "https://restv2.fireant.vn/symbols"


def fetch_FireAnt_stock(args: str) -> str:
    """
    Fetch historical stock data from FireAnt API for a given ticker and date range.
    Input: JSON string with keys "ticker", "start_date" (YYYY-MM-DD), "end_date" (YYYY-MM-DD).
    Example: {"ticker": "FPT", "start_date": "2025-01-01", "end_date": "2025-01-31"}
    Returns: JSON string with trading data (date, open, high, low, close, volume).
    """
    try:
        params = json.loads(args) if isinstance(args, str) else args
        ticker = params["ticker"].upper()
        start_date = params["start_date"]
        end_date = params["end_date"]
    except (json.JSONDecodeError, KeyError) as e:
        return f'Error: Invalid input. Expected JSON with "ticker", "start_date", "end_date". Got: {e}'

    try:
        url = f"{BASE_URL}/{ticker}/historical-quotes?startDate={start_date}&endDate={end_date}&offset=0&limit=20"
        headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return f"No trading data found for {ticker} from {start_date} to {end_date}."

        result = []
        for item in data:
            result.append({
                "ticker": ticker,
                "date": datetime.datetime.strptime(item["date"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d"),
                "open": item.get("priceOpen", 0),
                "high": item.get("priceHigh", 0),
                "low": item.get("priceLow", 0),
                "close": item.get("priceClose", 0),
                "volume": item.get("totalVolume", 0),
            })

        return json.dumps(result, ensure_ascii=False)

    except requests.exceptions.Timeout:
        return f"Error: Request timed out for ticker '{ticker}'."
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


# ── Tool 3: Compare Stocks ─────────────────────────────────────

def compare_stocks(args: str) -> str:
    """
    Compare the recent price performance of two Vietnamese stocks.
    Input: JSON string with keys "ticker1" and "ticker2".
    Example: {"ticker1": "FPT", "ticker2": "VNM"}
    Returns: percentage change of each stock over the latest 5 trading days and which one performed better.
    """
    try:
        params = json.loads(args) if isinstance(args, str) else args
        ticker1 = params["ticker1"].upper()
        ticker2 = params["ticker2"].upper()
    except (json.JSONDecodeError, KeyError) as e:
        return f'Error: Invalid input. Expected JSON with "ticker1" and "ticker2". Got: {e}'

    data1 = fetch_Cafef_stock(ticker1)
    data2 = fetch_Cafef_stock(ticker2)

    if data1.startswith("Error"):
        return data1
    if data2.startswith("Error"):
        return data2

    try:
        prices1 = json.loads(data1)
        prices2 = json.loads(data2)

        change1 = (prices1[-1]["close"] - prices1[0]["close"]) / prices1[0]["close"] * 100
        change2 = (prices2[-1]["close"] - prices2[0]["close"]) / prices2[0]["close"] * 100

        winner = ticker1 if change1 > change2 else ticker2 if change2 > change1 else "Draw"

        result = {
            ticker1: {
                "start_close": prices1[0]["close"],
                "end_close": prices1[-1]["close"],
                "change_pct": round(change1, 2),
            },
            ticker2: {
                "start_close": prices2[0]["close"],
                "end_close": prices2[-1]["close"],
                "change_pct": round(change2, 2),
            },
            "winner": winner,
        }
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return f"Error comparing stocks: {str(e)}"

# ── Tool 4: Calculate ─────────────────────────────────────────

def calculate(args: str) -> str:
    """
    Perform a calculation on a list of numbers.
    Input: JSON string with keys "operation" and "values".
    Supported operations: "sum", "average", "min", "max", "change_pct".
    - "change_pct" calculates percentage change from first to last value.
    Example: {"operation": "average", "values": [95000, 93000, 91000]}
    Returns: the calculation result as a string.
    """
    try:
        params = json.loads(args) if isinstance(args, str) else args
        operation = params["operation"].lower()
        values = params["values"]
    except (json.JSONDecodeError, KeyError) as e:
        return f'Error: Invalid input. Expected JSON with "operation" and "values". Got: {e}'

    if not isinstance(values, list) or len(values) == 0:
        return "Error: 'values' must be a non-empty list of numbers."

    try:
        values = [float(v) for v in values]
    except (ValueError, TypeError):
        return "Error: All values must be numbers."

    if operation == "sum":
        return f"{sum(values)}"
    elif operation == "average":
        return f"{sum(values) / len(values)}"
    elif operation == "min":
        return f"{min(values)}"
    elif operation == "max":
        return f"{max(values)}"
    elif operation == "change_pct":
        if values[0] == 0:
            return "Error: First value cannot be zero for percentage change."
        pct = (values[-1] - values[0]) / values[0] * 100
        return f"{round(pct, 2)}%"
    else:
        return f"Error: Unknown operation '{operation}'. Supported: sum, average, min, max, change_pct."


# ── Tool Registry (for ReAct Agent) ───────────────────────────

STOCK_TOOLS = [
    {
        "name": "fetch_CafeF_stock",
        "description": "Fetch the latest 5 trading days of a Vietnamese stock from Cafef. Input: stock ticker symbol as a string (e.g. 'VNM', 'FPT').",
        "function": fetch_Cafef_stock,
    },
    {
        "name": "fetch_FireAnt_stock",
        "description": 'Fetch historical stock data from FireAnt for a date range. Input: JSON string with "ticker", "start_date" (YYYY-MM-DD), "end_date" (YYYY-MM-DD). Example: {"ticker": "FPT", "start_date": "2025-01-01", "end_date": "2025-01-31"}',
        "function": fetch_FireAnt_stock,
    },
    {
        "name": "compare_stocks",
        "description": 'Compare price performance of two Vietnamese stocks over the latest 5 trading days. Input: JSON string with "ticker1" and "ticker2". Example: {"ticker1": "FPT", "ticker2": "VNM"}',
        "function": compare_stocks,
    },
    {
        "name": "calculate",
        "description": 'Perform math on a list of numbers. Input: JSON string with "operation" (sum/average/min/max/change_pct) and "values" (list of numbers). Example: {"operation": "average", "values": [95000, 93000, 91000]}',
        "function": calculate,
    },
]

# ── Tool 5: Summarize Stock ───────────────────────────────────

def summarize_stock(args: str) -> str:
    """
    Summarize the latest 5 trading days of a Vietnamese stock.
    Input: JSON string with key "ticker".
    Example: {"ticker": "FPT"}
    Returns: JSON string with summary statistics including latest close,
    average close, highest high, lowest low, total volume, and change percentage.
    """
    try:
        params = json.loads(args) if isinstance(args, str) else args
        ticker = params["ticker"].upper()
    except (json.JSONDecodeError, KeyError) as e:
        return f'Error: Invalid input. Expected JSON with "ticker". Got: {e}'

    data = fetch_Cafef_stock(ticker)
    if data.startswith("Error"):
        return data

    try:
        prices = json.loads(data)

        if not isinstance(prices, list) or len(prices) == 0:
            return f"Error: No data found for ticker '{ticker}'."

        close_prices = [item["close"] for item in prices]
        high_prices = [item["high"] for item in prices]
        low_prices = [item["low"] for item in prices]
        volumes = [item["volume"] for item in prices]

        start_close = close_prices[0]
        latest_close = close_prices[-1]
        change_pct = 0 if start_close == 0 else round((latest_close - start_close) / start_close * 100, 2)

        result = {
            "ticker": ticker,
            "period": {
                "start_date": prices[0]["date"],
                "end_date": prices[-1]["date"],
            },
            "latest_close": latest_close,
            "average_close": round(sum(close_prices) / len(close_prices), 2),
            "highest_high": max(high_prices),
            "lowest_low": min(low_prices),
            "total_volume": sum(volumes),
            "change_pct": change_pct,
        }
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return f"Error summarizing stock: {str(e)}"


# ── Add to Tool Registry ──────────────────────────────────────

STOCK_TOOLS.append(
    {
        "name": "summarize_stock",
        "description": 'Summarize the latest 5 trading days of a Vietnamese stock. Input: JSON string with "ticker". Example: {"ticker": "FPT"}',
        "function": summarize_stock,
    }
)