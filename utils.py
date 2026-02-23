# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import aiohttp
import asyncio
import logging
from config import (
    CRYPTO_API_TOKEN_MAINNET, CRYPTO_API_TOKEN_TESTNET,
    CRYPTO_API_URLS, INVOICE_TIMEOUT, INVOICE_CHECK_INTERVAL,
    DISPLAY_TIMEOUT, LOG_CHAT_ID, ADMIN_ID
)
from database import db

logger = logging.getLogger(__name__)

# ========== УТИЛИТЫ ==========
def format_number(num: float) -> str:
    if num == 0:
        return "0"
    return f"{num:,.2f}".replace(",", " ")

def get_vip_progress(total_bets: float):
    if total_bets < 100:
        progress = (total_bets / 100) * 100
        return f"0️⃣ Новичок ➡️ 1️⃣ Бронза", progress
    elif total_bets < 500:
        progress = ((total_bets - 100) / 400) * 100
        return f"1️⃣ Бронза ➡️ 2️⃣ Серебро", progress
    elif total_bets < 1000:
        progress = ((total_bets - 500) / 500) * 100
        return f"2️⃣ Серебро ➡️ 3️⃣ Золото", progress
    elif total_bets < 5000:
        progress = ((total_bets - 1000) / 4000) * 100
        return f"3️⃣ Золото ➡️ 4️⃣ Платина", progress
    else:
        progress = 100
        return f"4️⃣ Платина ➡️ 5️⃣ Бриллиант", progress

def get_user_rank(total_bets: float) -> str:
    if total_bets >= 5000:
        return "5️⃣ Бриллиант"
    elif total_bets >= 1000:
        return "4️⃣ Платина"
    elif total_bets >= 500:
        return "3️⃣ Золото"
    elif total_bets >= 100:
        return "2️⃣ Серебро"
    else:
        return "1️⃣ Бронза"

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_valid_amount(text: str) -> bool:
    if not text:
        return False
    text = text.replace(' ', '').replace(',', '.')
    try:
        float(text)
        return True
    except ValueError:
        return False

def get_game_key_by_command(command: str) -> str:
    mapping = {"/cube": "dice", "/dice": "dice", "/foot": "football", "/basket": "basketball", "/bowl": "bowling", "/darts": "darts", "/slots": "slots"}
    return mapping.get(command, "dice")

def pluralize(count: int, one: str, few: str, many: str) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return one
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return few
    else:
        return many

# ========== CRYPTO PAY API ==========
class CryptoPayAPI:
    def __init__(self):
        self.network = db.get_network()
        self.update_token()
        self.pending_invoices = {}
        self.session = None
        self.bot = None
    
    def set_bot(self, bot):
        self.bot = bot
    
    def update_token(self):
        self.api_token = CRYPTO_API_TOKEN_MAINNET if self.network == "mainnet" else CRYPTO_API_TOKEN_TESTNET
        self.base_url = CRYPTO_API_URLS[self.network]
        self.headers = {"Crypto-Pay-API-Token": self.api_token, "Content-Type": "application/json"}
    
    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            session = await self.get_session()
            if method == 'GET':
                async with session.get(url, headers=self.headers, params=data) as resp:
                    return await resp.json()
            else:
                async with session.post(url, headers=self.headers, json=data) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"API Request error: {e}")
            return None
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def create_invoice(self, amount: float, user_id: int) -> Optional[Dict]:
        payload = {
            'asset': 'USDT', 'amount': str(amount), 'description': f"Депозит для пользователя {user_id}",
            'payload': str(user_id), 'allow_comments': False, 'allow_anonymous': False, 'expires_in': INVOICE_TIMEOUT
        }
        response = await self._request('POST', '/createInvoice', payload)
        if response and response.get('ok'):
            result = response['result']
            return {'invoice_id': result['invoice_id'], 'pay_url': result['pay_url'], 'amount': result['amount']}
        return None
    
    async def check_invoice(self, invoice_id: int) -> str:
        response = await self._request('GET', '/getInvoices', {'invoice_ids': str(invoice_id)})
        if response and response.get('ok') and response['result'].get('items'):
            return response['result']['items'][0].get('status')
        return 'not_found'
    
    async def delete_invoice(self, invoice_id: int) -> bool:
        response = await self._request('POST', '/deleteInvoice', {'invoice_id': invoice_id})
        return response and response.get('ok')
    
    async def transfer(self, user_id: int, amount: float) -> Optional[Dict]:
        spend_id = f"{int(datetime.now().timestamp())}_{user_id}"
        payload = {'user_id': user_id, 'asset': 'USDT', 'amount': str(amount), 'spend_id': spend_id, 'comment': 'Вывод из BeeCube'}
        response = await self._request('POST', '/transfer', payload)
        if response and response.get('ok'):
            return response['result']
        return None
    
    def add_pending_invoice(self, invoice_id: int, user_id: int, amount: float, pay_url: str, message):
        self.pending_invoices[invoice_id] = {
            'user_id': user_id, 'amount': amount, 'pay_url': pay_url,
            'expire_time': datetime.now() + timedelta(seconds=INVOICE_TIMEOUT),
            'processed': False, 'last_check': datetime.now(),
            'chat_id': message.chat.id
        }
    
    async def check_pending_invoices(self):
        while True:
            try:
                current_time = datetime.now()
                to_remove = []
                for invoice_id, data in self.pending_invoices.items():
                    if data.get('processed'):
                        to_remove.append(invoice_id)
                        continue
                    if (current_time - data['last_check']).total_seconds() < INVOICE_CHECK_INTERVAL:
                        continue
                    data['last_check'] = current_time
                    if current_time > data['expire_time']:
                        await self.delete_invoice(invoice_id)
                        try:
                            await self.bot.send_message(
                                chat_id=data['chat_id'],
                                text=f"❌ Время оплаты истекло\n\nСумма: ${data['amount']:.2f}"
                            )
                        except:
                            pass
                        to_remove.append(invoice_id)
                        continue
                    status = await self.check_invoice(invoice_id)
                    if status == 'paid':
                        if await db.update_balance(data['user_id'], data['amount']):
                            saved = await db.save_transaction(
                                data['user_id'], 'deposit', data['amount'], 'completed', 
                                invoice_id=invoice_id, invoice_url=data['pay_url']
                            )
                            if saved:
                                data['processed'] = True
                                new_balance = db.get_balance(data['user_id'])
                                await log_deposit(data['user_id'], data['amount'])
                                try:
                                    await self.bot.send_message(
                                        chat_id=data['chat_id'],
                                        text=f"✅ Счет оплачен!\n\nСумма: +${data['amount']:.2f}\nНовый баланс: ${new_balance:.2f}"
                                    )
                                except:
                                    pass
                                to_remove.append(invoice_id)
                for invoice_id in to_remove:
                    if invoice_id in self.pending_invoices:
                        del self.pending_invoices[invoice_id]
            except Exception as e:
                logger.error(f"Error in check_pending_invoices: {e}")
            await asyncio.sleep(1)

crypto = CryptoPayAPI()

# ========== ФУНКЦИИ ЛОГОВ ==========
async def log_deposit(user_id: int, amount: float):
    try:
        user = db.get_user(user_id)
        name = user['first_name'] if user else f"ID {user_id}"
        username = f"@{user['username']}" if user and user['username'] else "без username"
        await crypto.bot.send_message(LOG_CHAT_ID, f"💰 ДЕПОЗИТ\n\nПользователь: {name} ({username})\nID: {user_id}\nСумма: ${amount:.2f}")
    except Exception as e:
        logger.error(f"Failed to log deposit: {e}")

async def log_withdraw(user_id: int, amount: float, status: str):
    try:
        user = db.get_user(user_id)
        name = user['first_name'] if user else f"ID {user_id}"
        username = f"@{user['username']}" if user and user['username'] else "без username"
        emoji = "✅" if status == "completed" else "❌"
        await crypto.bot.send_message(LOG_CHAT_ID, f"{emoji} ВЫВОД\n\nПользователь: {name} ({username})\nID: {user_id}\nСумма: ${amount:.2f}\nСтатус: {status}")
    except Exception as e:
        logger.error(f"Failed to log withdraw: {e}")

async def log_big_win(user_id: int, game: str, bet: float, win: float):
    try:
        user = db.get_user(user_id)
        name = user['first_name'] if user else f"ID {user_id}"
        username = f"@{user['username']}" if user and user['username'] else "без username"
        await crypto.bot.send_message(LOG_CHAT_ID, f"🎉 КРУПНЫЙ ВЫИГРЫШ\n\nПользователь: {name} ({username})\nID: {user_id}\nИгра: {game}\nСтавка: ${bet:.2f}\nВыигрыш: +${win:.2f}")
    except Exception as e:
        logger.error(f"Failed to log big win: {e}")

async def log_pvp_game(chat_id: int, creator_id: int, opponent_id: int, game_type: str, bet: float, winner_id: int, win_amount: float):
    try:
        creator = db.get_user(creator_id)
        opponent = db.get_user(opponent_id)
        winner = "Создатель" if winner_id == creator_id else "Противник"
        await crypto.bot.send_message(LOG_CHAT_ID, f"⚔️ PVP ИГРА\n\nЧат: {chat_id}\nИгра: {game_type}\nСтавка: ${bet:.2f}\nСоздатель: {creator['first_name']} (@{creator['username']})\nПротивник: {opponent['first_name']} (@{opponent['username']})\nПобедитель: {winner}\nВыигрыш: ${win_amount:.2f}")
    except Exception as e:
        logger.error(f"Failed to log pvp game: {e}")

async def log_admin_balance(user_id: int, amount: float, admin_id: int, action: str):
    try:
        user = db.get_user(user_id)
        admin = db.get_user(admin_id)
        name = user['first_name'] if user else f"ID {user_id}"
        username = f"@{user['username']}" if user and user['username'] else "без username"
        admin_name = admin['first_name'] if admin else f"ID {admin_id}"
        action_text = "НАЧИСЛЕНИЕ" if amount > 0 else "СПИСАНИЕ"
        emoji = "➕" if amount > 0 else "➖"
        await crypto.bot.send_message(LOG_CHAT_ID, f"{emoji} АДМИН {action_text}\n\nАдмин: {admin_name}\nПользователь: {name} ({username})\nID: {user_id}\nСумма: ${abs(amount):.2f}")
    except Exception as e:
        logger.error(f"Failed to log admin balance: {e}")