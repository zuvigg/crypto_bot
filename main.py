import requests
import time
import telebot
from binance.client import Client

# Конфигурация
BINANCE_API_KEY = "6GgTf3eDcPs3Zle1PJzRSfgt6ay4ynYBnCDncJxF6Hu7bHjdHIBASpsexfXsyCX0"
BINANCE_SECRET_KEY = "gaSPV8vLcVu7nmJL2jCH6NQiMh7h5nU3kt5p8QPkTOyNp0FCkZ4oi9ecldXrwUjc"
TELEGRAM_BOT_TOKEN = "8034186947:AAFljqSGjx49tiN4D2fP8XN7au6IofOZDFg"
TELEGRAM_CHAT_ID = "977501740"

# Пороговое значение изменения цены в %
PRICE_CHANGE_THRESHOLD = 3.0  # Например, 3%
CHECK_INTERVAL = 60  # Время между проверками (в секундах)

# Инициализация клиентов
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# Функция отправки уведомления
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)


# Функция мониторинга цен
previous_prices = {}


def monitor_prices():
    global previous_prices
    try:
        tickers = binance_client.get_ticker()

        for ticker in tickers:
            symbol = ticker['symbol']
            if not symbol.endswith("USDT"):
                continue

            last_price = float(ticker['lastPrice'])

            if symbol in previous_prices:
                old_price = previous_prices[symbol]
                if old_price == 0:
                    continue  # Пропускаем, если старая цена равна 0

                price_change = ((last_price - old_price) / old_price) * 100

                if abs(price_change) >= PRICE_CHANGE_THRESHOLD:
                    message = f"⚡ {symbol}: резкое изменение цены {price_change:.2f}% ({old_price} → {last_price})"
                    send_telegram_message(message)
                    print(message)

            previous_prices[symbol] = last_price
    except Exception as e:
        print(f"Ошибка мониторинга: {e}")
        time.sleep(5)  # Подождем 5 секунд перед повторной попыткой

# Функция получения текущей цены актива
def get_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return f"Текущая цена {symbol}: {ticker['price']} USDT"
    except Exception as e:
        return f"Ошибка получения цены: {e}"


# Функция получения топ-5 активов по росту
def get_top_gainers():
    tickers = binance_client.get_ticker()
    changes = [(t['symbol'], float(t['priceChangePercent'])) for t in tickers if t['symbol'].endswith("USDT")]
    top_gainers = sorted(changes, key=lambda x: x[1], reverse=True)[:5]
    return "🔥 Топ-5 активов по росту:\n" + "\n".join([f"{s}: {p:.2f}%" for s, p in top_gainers])


# Обработка команд Telegram
@telegram_bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    telegram_bot.reply_to(message,
                          "Привет! Я бот для мониторинга криптовалют. Доступные команды:\n/start - Начать\n/help - Справка\n/price SYMBOL - Узнать текущую цену актива (пример: /price BTCUSDT)\n/top - Топ-5 активов по росту")


@telegram_bot.message_handler(commands=['price'])
def send_price(message):
    try:
        symbol = message.text.split()[1].upper()
        response = get_price(symbol)
    except IndexError:
        response = "Пожалуйста, укажите символ актива (пример: /price BTCUSDT)"
    telegram_bot.reply_to(message, response)


@telegram_bot.message_handler(commands=['top'])
def send_top_gainers(message):
    response = get_top_gainers()
    telegram_bot.reply_to(message, response)


# Запуск бота
if __name__ == "__main__":
    import threading


    # Запускаем мониторинг в отдельном потоке
    def run_monitor():
        while True:
            try:
                monitor_prices()
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(10)


    monitoring_thread = threading.Thread(target=run_monitor, daemon=True)
    monitoring_thread.start()

    # Запускаем бота
    telegram_bot.polling(none_stop=True)
