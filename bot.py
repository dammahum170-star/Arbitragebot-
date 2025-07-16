import ccxt
import time
import requests

# ✅ Telegram
TELEGRAM_TOKEN = "7080165884:AAFqBmS6b6EDj_WZdP0YenJ9vmi7NoqCIKk"
CHAT_ID = "7865925097"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

# ✅ Настройки
SPREAD_MIN = 1.0
SPREAD_MAX = 5.0
VOLUME_MIN = 10_000

# ✅ Комиссии, фандинг, плечо
FEES = {
    "binance": {"trade": 0.1, "withdraw": 1.0, "funding": 0.02, "leverage": 5},
    "bybit": {"trade": 0.1, "withdraw": 1.5, "funding": 0.03, "leverage": 5},
    "kucoin": {"trade": 0.1, "withdraw": 1.2, "funding": 0.01, "leverage": 5},
    "bitget": {"trade": 0.1, "withdraw": 0.9, "funding": 0.015, "leverage": 5},
    "mexc": {"trade": 0.1, "withdraw": 1.3, "funding": 0.02, "leverage": 5},
    "gateio": {"trade": 0.15, "withdraw": 1.1, "funding": 0.025, "leverage": 5},
    "lbank": {"trade": 0.1, "withdraw": 1.0, "funding": 0.018, "leverage": 5},
    "okx": {"trade": 0.1, "withdraw": 1.0, "funding": 0.02, "leverage": 5},
}

# ✅ Подключение к биржам
EXCHANGES = {
    "binance": ccxt.binance(),
    "bybit": ccxt.bybit(),
    "kucoin": ccxt.kucoin(),
    "bitget": ccxt.bitget(),
    "mexc": ccxt.mexc(),
    "gateio": ccxt.gateio(),
    "lbank": ccxt.lbank(),
    "okx": ccxt.okx(),
}

# ✅ Получение цен
def get_all_prices():
    result = []
    for name, ex in EXCHANGES.items():
        try:
            markets = ex.load_markets()
            for symbol in markets:
                if "/USDT" not in symbol:
                    continue
                try:
                    ticker = ex.fetch_ticker(symbol)
                    price = {
                        "symbol": symbol,
                        "ask": ticker['ask'],
                        "bid": ticker['bid'],
                        "volume": ticker.get('quoteVolume') or 0,
                        "exchange": name,
                    }
                    if price['ask'] and price['bid']:
                        result.append(price)
                except:
                    continue
        except Exception as e:
            print(f"Ошибка {name}: {e}")
    return result

# ✅ Лог
def log_signal(msg):
    with open("log.txt", "a") as f:
        f.write(msg + "\n")

# ✅ Главная функция
def main():
    send_telegram("🤖 Арбитражный бот запущен")
    while True:
        data = get_all_prices()
        by_symbol = {}
        for item in data:
            sym = item['symbol']
            by_symbol.setdefault(sym, []).append(item)

        for symbol, quotes in by_symbol.items():
            for a in quotes:
                for b in quotes:
                    if a['exchange'] == b['exchange']:
                        continue

                    ask = a['ask']
                    bid = b['bid']
                    if not ask or not bid:
                        continue

                    spread = (bid - ask) / ask * 100
                    if not (SPREAD_MIN <= spread <= SPREAD_MAX):
                        continue

                    fee_buy = FEES.get(a['exchange'], {}).get("trade", 0.1)
                    fee_sell = FEES.get(b['exchange'], {}).get("trade", 0.1)
                    withdraw_fee = FEES.get(a['exchange'], {}).get("withdraw", 1.0)
                    funding = FEES.get(b['exchange'], {}).get("funding", 0.0)
                    leverage = FEES.get(b['exchange'], {}).get("leverage", 1)

                    net_profit = (spread - fee_buy - fee_sell - funding - (withdraw_fee / ask * 100)) * leverage
                    vol = min(a['volume'], b['volume']) * ask

                    if vol < VOLUME_MIN or net_profit < SPREAD_MIN:
                        continue

                    msg = (
                        f"\n📈 Арбитраж {symbol}\n"
                        f"🔁 {a['exchange'].upper()} (LONG) ➡ {b['exchange'].upper()} (SHORT)\n"
                        f"🟢 Купить: {ask:.2f} ({fee_buy}% fee)\n"
                        f"🔴 Продать: {bid:.2f} ({fee_sell}% fee)\n"
                        f"📊 Спред: {spread:.2f}% | Фандинг: {funding}%\n"
                        f"💸 Комиссия на вывод: ${withdraw_fee}\n"
                        f"⚖ Плечо: x{leverage}\n"
                        f"✅ Чистый профит: {net_profit:.2f}%\n"
                        f"📦 Объём: ${vol:,.0f}"
                    )
                    print(msg)
                    send_telegram(msg)
                    log_signal(msg)

        time.sleep(120)

# ✅ Запуск
if __name__ == "__main__":
    main()
