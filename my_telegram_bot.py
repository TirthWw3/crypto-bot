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
# Replace these with your actual new, secure Binance API credentials

BINANCE_API_SECRET = os.getenv('SECURE_KEY')
BINANCE_API_KEY = os.getenv('API_KEY')

# Your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7035494499:AAE1YTjSKRCdat2kGI43aZdGppOWbajqrqg'
CHAT_ID = 489313762  # Replace with your actual chat ID

# Initialize the Binance and Telegram Bot
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True
})

# Synchronize the system time with Binance server time
exchange.load_time_difference()

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def calculate_ema(prices, length):
    """Calculate the Exponential Moving Average for a list of prices."""
    return prices.ewm(span=length).mean()

def check_ema_and_send_alert(symbol):
    """Fetch historical data, calculate 200-day EMA, and send a Telegram alert."""
    try:
        # Fetch historical price data
        candles = exchange.fetch_ohlcv(symbol, '1d', limit=200)
        high_prices = [candle[2] for candle in candles]  # Extract the high prices
        high_series = pd.Series(high_prices)

        # Calculate the 200-day EMA from high prices
        ema200 = calculate_ema(high_series, 200).iloc[-1]
        current_high = high_series.iloc[-1]

        # Check if the current high is greater than the 200-day EMA
        if current_high > ema200:
            message = f"{symbol}: Current high {current_high} is above the 200-day EMA {ema200}"
            bot.send_message(CHAT_ID, message)
            logging.info(f"Alert sent for {symbol}: {message}")
        else:
            logging.info(f"No alert for {symbol}: Current high {current_high} is below the 200-day EMA {ema200}")
    except Exception as e:
        logging.error(f"Error checking {symbol}: {str(e)}")

def main():
    # List of symbols to check
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'SPA/USDT', 'ARB/USDT', 'DYDX/USDT']  # Add more symbols as needed

    # Check each symbol and send alerts
    for symbol in symbols:
        check_ema_and_send_alert(symbol)
        time.sleep(1)  # Sleep to prevent hitting API rate limits

if __name__ == "__main__":
    main()
