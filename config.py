# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
import logging
from typing import Dict
from aiogram.fsm.state import State, StatesGroup

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8272217145:AAFscvlrXU131_cLtN-xa4lwWor_nMv0HH4"
CRYPTO_API_TOKEN_MAINNET = "28352"
CRYPTO_API_TOKEN_TESTNET = "2692"
ADMIN_ID = 7988509200
LOG_CHAT_ID = -5253103182
MIN_BET_DEFAULT = 1
MIN_DEPOSIT_DEFAULT = 1
MIN_WITHDRAW_DEFAULT = 1
WITHDRAW_FEE = 0.1  # 10% комиссия (скрытая)
CRYPTO_NETWORK = "testnet"
DATABASE_PATH = "casino.db"
INVOICE_TIMEOUT = 40
INVOICE_CHECK_INTERVAL = 3
DISPLAY_TIMEOUT = 60
PVP_MULTIPLIER_DEFAULT = 1.8
CACHE_TTL = 60

CRYPTO_API_URLS = {
    "mainnet": "https://pay.crypt.bot/api",
    "testnet": "https://testnet-pay.crypt.bot/api"
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameStates(StatesGroup):
    waiting_for_bet = State()
    game_key = State()
    waiting_for_deposit = State()

class PromoStates(StatesGroup):
    waiting_for_code = State()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_ban_reason = State()
    waiting_for_balance_amount = State()
    waiting_for_balance_user_id = State()
    waiting_for_balance_action = State()
    waiting_for_message = State()
    waiting_for_mailing_text = State()
    waiting_for_promo_code = State()
    waiting_for_promo_amount = State()
    waiting_for_promo_uses = State()
    waiting_for_search_query = State()
    waiting_for_game_multiplier = State()
    waiting_for_game_index = State()
    waiting_for_min_bet = State()
    waiting_for_min_deposit = State()
    waiting_for_min_withdraw = State()
    waiting_for_withdraw_fee = State()  # Добавляем состояние для комиссии
    waiting_for_pvp_multiplier = State()
    waiting_for_stats_user_id = State()
    waiting_for_stats_field = State()
    waiting_for_stats_value = State()
    waiting_for_top_position = State()
    waiting_for_top_user_id = State()
    waiting_for_top_value = State()

GAME_RULES = {
    "slots": {"name": "СЛОТЫ", "emoji": "🎰", "command": "slots", "win_values": [1, 22, 43, 64], "multiplier": 10, "win_text": "ДЖЕКПОТ! x10", "description_key": "🎰"},
    "bowling": {"name": "БОУЛИНГ", "emoji": "🎳", "command": "bowl", "win_values": [6], "multiplier": 6, "win_text": "СТРАЙК! x6", "description_key": "🎳"},
    "football": {"name": "ФУТБОЛ", "emoji": "⚽", "command": "foot", "win_values": [4, 5], "multiplier": 1.8, "win_text": "ГОЛ! x1.8", "description_key": "⚽"},
    "basketball": {"name": "БАСКЕТ", "emoji": "🏀", "command": "basket", "win_values": [4, 5], "multiplier": 1.8, "win_text": "ПОПАДАНИЕ! x1.8", "description_key": "🏀"},
    "darts": {"name": "ДАРТС", "emoji": "🎯", "command": "darts", "win_values": [6], "multiplier": 5, "win_text": "ЯБЛОЧКО! x5", "description_key": "🎯"},
    "dice": {"name": "КУБИК", "emoji": "🎲", "command": "cube", "win_values": [4, 5, 6], "multiplier": {4: 1.4, 5: 1.6, 6: 1.9}, "win_text": {4: "4 - x1.4", 5: "5 - x1.6", 6: "6 - x1.9"}, "description_key": "🎲"}
}

THROW_DESCRIPTIONS = {
    "⚽": {1: "Слабый удар", 2: "Мимо ворот", 3: "Штанга", 4: "ГОЛ!", 5: "Красивый гол!", 6: "Шедевр!"},
    "🏀": {1: "Мимо кольца", 2: "Дужка", 3: "Щит", 4: "Попадание!", 5: "Точное попадание!", 6: "Слам-данк!"},
    "🎯": {1: "В молоко", 2: "Близко", 3: "Сектор 20", 4: "Тройное", 5: "Бычий глаз!", 6: "ЯБЛОЧКО!"},
    "🎳": {1: "Желоб", 2: "Одна кегля", 3: "Три кегли", 4: "Пять кеглей", 5: "Спейр", 6: "СТРАЙК!"},
    "🎰": {1: "Джекпот!", 22: "Джекпот!", 43: "Джекпот!", 64: "Джекпот!"},
    "🎲": {1: "Змеиные глаза", 2: "Двойка", 3: "Тройка", 4: "Четверка", 5: "Пятерка", 6: "Шестерка"}
