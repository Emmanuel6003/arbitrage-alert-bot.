import os
import time
import requests

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = None  # Auto-detects on first run
API_URL = "https://api.bybit.com"
TOKENS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "TRX",
    "LINK", "MATIC", "LTC", "SHIB", "ATOM", "UNI", "ETC", "BCH", "XLM", "APT",
    "SAND", "AAVE", "NEAR", "FTM", "EGLD", "IMX", "HBAR", "RNDR", "GRT", "AR"
]
MIN_SPREAD = float(os.getenv("MIN_SPREAD", 0.05))  # Default 0.05%

# === FUNCTIONS ===
def fetch_all_prices():
    """Fetch all spot ticker prices in one request."""
    url = f"{API_URL}/v5/market/tickers?category=spot"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "result" in data and "list" in data["result"]:
            prices = {}
            for ticker in data["result"]["list"]:
                symbol = ticker["symbol"]
                prices[symbol] = float(ticker["lastPrice"])
            return prices
    except Exception as e:
        print(f"[ERROR fetching all prices] {e}")
    return {}

def send_telegram_message(message: str):
    """Send a message to Telegram bot."""
    global CHAT_ID
    if CHAT_ID is None:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates").json()
            if updates.get("ok") and updates.get("result"):
                CHAT_ID = updates["result"][-1]["message"]["chat"]["id"]
                print(f"[INFO] Auto-detected CHAT_ID: {CHAT_ID}")
        except Exception as e:
            print(f"[ERROR detecting chat ID] {e}")
            return
    if CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {'chat_id': CHAT_ID, 'text': message}
            requests.post(url, data=payload)
        except Exception as e:
            print(f"[Telegram ERROR] {e}")

def check_arbitrage():
    """Check for arbitrage between USDT and USDC pairs."""
    print("🔍 Checking arbitrage opportunities...")
    prices = fetch_all_prices()
    if not prices:
        print("[WARN] No prices fetched this round.")
        return

    for token in TOKENS:
        pair_usdt = f"{token}USDT"
        pair_usdc = f"{token}USDC"

        if pair_usdt in prices and pair_usdc in prices:
            price_usdt = prices[pair_usdt]
            price_usdc = prices[pair_usdc]
            diff = abs(price_usdt - price_usdc)
            avg = (price_usdt + price_usdc) / 2
            diff_percent = (diff / avg) * 100

            if diff_percent >= MIN_SPREAD:
                direction = "Buy USDT 🔻 / Sell USDC 🔺" if price_usdt < price_usdc else "Buy USDC 🔻 / Sell USDT 🔺"
                msg = (
                    f"📢 Arbitrage Alert: [{token}]\n"
                    f"USDT: {price_usdt:.4f} | USDC: {price_usdc:.4f}\n"
                    f"🔁 Spread: {diff_percent:.4f}%\n"
                    f"💡 {direction}"
                )
                print(msg)
                send_telegram_message(msg)

# === MAIN LOOP ===
if __name__ == "__main__":
    print("🚀 Arbitrage bot started! Scanning every 120 seconds...")
    while True:
        check_arbitrage()
        time.sleep(120)
