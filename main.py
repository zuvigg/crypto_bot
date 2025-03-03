import io

import requests
import time
import telebot
from binance.client import Client
import os
from dotenv import load_dotenv
from matplotlib import pyplot as plt

# Загружаем переменные из .env
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "977501740"

# Пороговое значение изменения цены в % и интервал проверки
PRICE_CHANGE_THRESHOLD = 3.0
CHECK_INTERVAL = 60

# Инициализация клиентов
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Функция отправки уведомления
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

# Отправляем сообщение о запуске бота
send_telegram_message("🤖 Бот запущен и мониторит рынок!")

# Функция получения текущей цены актива
def get_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return f"Текущая цена {symbol}: {ticker['price']} USDT"
    except Exception as e:
        return f"Ошибка получения цены: {e}"


# Функция получения цены 10 минут назад
def get_price_10m_ago(symbol):
    try:
        klines = binance_client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        return float(klines[0][1])  # Открытая цена 10 минут назад
    except Exception as e:
        return None

# Функция получения текущей цены актива
def get_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        return None

# Функция трендов за последние 10 минут
def get_trend_last(n):
    tickers = binance_client.get_ticker()
    symbols = [t['symbol'] for t in tickers if t['symbol'].endswith("USDT")]
    changes = []

    # Отправка сообщения о начале анализа и получение ID сообщения
    progress_response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "📊 Анализируем рынок... 0%"
    })

    # Извлекаем ID сообщения
    progress_data = progress_response.json()
    message_id = progress_data.get("result", {}).get("message_id")
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        old_price = get_price_10m_ago(symbol)
        current_price = get_price(symbol)

        if old_price and current_price:
            price_change = ((current_price - old_price) / old_price) * 100
            changes.append((symbol, price_change))

        # Обновление прогресса
        progress_percent = int((i + 1) / total * 100)
        if progress_percent % 5 == 0:  # Обновлять каждые 10%
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText", json={
                "chat_id": TELEGRAM_CHAT_ID,
                "message_id": message_id,
                "text": f"📊 Анализируем рынок... {progress_percent}%"
            })
        print(f"Обработано {i}/{total}")

    top_changes = sorted(changes, key=lambda x: x[1], reverse=True)[:n]
    return "📈 Топ трендов за 10 минут:\n" + "\n".join([f"{s}: {p:.2f}%" for s, p in top_changes])


# Функция получения топ-5 активов по росту
def get_top_gainers():
    tickers = binance_client.get_ticker()
    changes = [(t['symbol'], float(t['priceChangePercent'])) for t in tickers if t['symbol'].endswith("USDT")]
    top_gainers = sorted(changes, key=lambda x: x[1], reverse=True)[:5]
    return "🔥 Топ-5 активов по росту:\n" + "\n".join([f"{s}: {p:.2f}%" for s, p in top_gainers])

# Функция получения топ-5 активов по падению
def get_top_losers():
    tickers = binance_client.get_ticker()
    changes = [(t['symbol'], float(t['priceChangePercent'])) for t in tickers if t['symbol'].endswith("USDT")]
    top_losers = sorted(changes, key=lambda x: x[1])[:5]
    return "📉 Топ-5 активов по падению:\n" + "\n".join([f"{s}: {p:.2f}%" for s, p in top_losers])

# Функция получения графика (заглушка, можно интегрировать Matplotlib)
def get_chart(symbol):
    try:
        klines = binance_client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=24)
        prices = [float(k[4]) for k in klines]
        timestamps = [i for i in range(len(prices))]

        plt.figure(figsize=(8, 4))
        plt.plot(timestamps, prices, marker='o', linestyle='-')
        plt.xlabel("Часы")
        plt.ylabel("Цена (USDT)")
        plt.title(f"График {symbol} за 24 часа")
        plt.grid()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return img
    except Exception as e:
        return f"Ошибка получения графика: {e}"

# Функция установки алерта (заглушка)
def set_alert(symbol, price):
    return f"🔔 Уведомление установлено: {symbol} при {price} USDT (в разработке)"

# Функция отображения текущих настроек
def get_settings():
    return f"⚙️ Текущие настройки:\n- Порог изменения цены: {PRICE_CHANGE_THRESHOLD}%\n- Интервал проверки: {CHECK_INTERVAL} сек"

# Функция изменения настроек
def set_settings(threshold, interval):
    global PRICE_CHANGE_THRESHOLD, CHECK_INTERVAL
    PRICE_CHANGE_THRESHOLD = float(threshold)
    CHECK_INTERVAL = int(interval)
    return "✅ Настройки обновлены!"

# Обработка команд Telegram
@telegram_bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    telegram_bot.reply_to(message, "Привет! Я бот для мониторинга криптовалют. Доступные команды:\n"
        "🔹 /price SYMBOL - Узнать текущую цену актива (пример: /price BTCUSDT)\n"
        "🔹 /chart SYMBOL - График цены за 24 часа (пример: /chart BTCUSDT)\n"
        "🔹 /trending - Тренды рынка\n"
        "🔹 /alert SYMBOL PRICE - Уведомление при достижении цены (пример: /alert BTCUSDT 50000)\n"
        "🔹 /settings - Показать текущие настройки\n"
        "🔹 /set THRESHOLD INTERVAL - Установить порог и интервал (пример: /set 5 120)")

@telegram_bot.message_handler(commands=['price'])
def send_price(message):
    try:
        symbol = message.text.split()[1].upper()
        response = get_price(symbol)
    except IndexError:
        response = "Пожалуйста, укажите символ актива (пример: /price BTCUSDT)"
    telegram_bot.reply_to(message, response)

@telegram_bot.message_handler(commands=['chart'])
def send_chart(message):
    try:
        symbol = message.text.split()[1].upper()
        img = get_chart(symbol)
        if isinstance(img, str):
            telegram_bot.reply_to(message, img)
        else:
            telegram_bot.send_photo(message.chat.id, img)
    except IndexError:
        response = "Пожалуйста, укажите символ актива (пример: /chart BTCUSDT)"
        telegram_bot.reply_to(message, response)

@telegram_bot.message_handler(commands=['trending'])
def send_trending(message):
    gainers = get_top_gainers()
    losers = get_top_losers()
    response = f"{gainers}\n\n{losers}"
    telegram_bot.reply_to(message, response)

@telegram_bot.message_handler(commands=['alert'])
def send_alert(message):
    try:
        _, symbol, price = message.text.split()
        response = set_alert(symbol.upper(), price)
    except ValueError:
        response = "Использование: /alert SYMBOL PRICE (пример: /alert BTCUSDT 50000)"
    telegram_bot.reply_to(message, response)

@telegram_bot.message_handler(commands=['settings'])
def send_settings(message):
    response = get_settings()
    telegram_bot.reply_to(message, response)


@telegram_bot.message_handler(commands=['trend_last'])
def send_trend_last(message):
    try:
        n = int(message.text.split()[1])
        response = get_trend_last(n)
    except (IndexError, ValueError):
        response = "Использование: /trend_last [n] (пример: /trend_last 5)"
    telegram_bot.reply_to(message, response)


@telegram_bot.message_handler(commands=['set'])
def change_settings(message):
    try:
        _, threshold, interval = message.text.split()
        response = set_settings(threshold, interval)
    except ValueError:
        response = "Использование: /set THRESHOLD INTERVAL (пример: /set 5 120)"
    telegram_bot.reply_to(message, response)

# Запуск бота
if __name__ == "__main__":
    telegram_bot.polling(none_stop=True)
