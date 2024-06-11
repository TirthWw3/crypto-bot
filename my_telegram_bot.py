
import os
import ccxt
import pandas as pd
import telebot
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API credentials
BINANCE_API_SECRET = os.getenv('SECURE_KEY')
BINANCE_API_KEY = os.getenv('API_KEY')

# Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = os.getenv('TELE_TOKEN')
CHAT_ID = 489313762

# Initialize the Binance and Telegram Bot
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True
})

# Synchronize the system time with Binance server time
exchange.load_time_difference()

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def fetch_data(symbol, timeframe='1d', limit=200):
    """Fetch historical data from Binance."""
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_ema_high(df, length=200):
    """Calculate the 200 EMA using the high prices."""
    ema = df['high'].ewm(span=length).mean()
    return ema

def check_price_reaches_ema(df, symbol):
    """Check if the current price reaches the 200 EMA high and send an alert."""
    current_high = df['high'].iloc[-1]
    ema_high = calculate_ema_high(df).iloc[-1]

    if current_high >= ema_high:
        message = (
            f"🚨 {symbol} Alert 🚨\n"
            f"Price has reached the 200 EMA high.\n"
            f"Current High: {current_high}\n"
            f"200 EMA High: {ema_high}\n"
        )
        bot.send_message(CHAT_ID, message)
        logging.info(f"Alert sent for {symbol}: {message}")
    else:
        logging.info(f"No alert for {symbol}: Current High {current_high}, 200 EMA High {ema_high}")

def main():
    while True:
        try:
            # Fetch all symbols
            markets = exchange.load_markets()
            symbols = [symbol for symbol in markets if '/USDT' in symbol]  # Filter for USDT pairs

            # Check each symbol and send alerts
            for symbol in symbols:
                try:
                    df = fetch_data(symbol)
                    check_price_reaches_ema(df, symbol)
                    time.sleep(1)  # Sleep to prevent hitting API rate limits
                except Exception as e:
                    logging.error(f"Error processing {symbol}: {str(e)}")

        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
        time.sleep(60 * 15)  # Wait for 15 minutes before the next analysis

if __name__ == "__main__":
    main()
