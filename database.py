# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
import sqlite3
import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from config import DATABASE_PATH, GAME_RULES, MIN_BET_DEFAULT, MIN_DEPOSIT_DEFAULT, MIN_WITHDRAW_DEFAULT, PVP_MULTIPLIER_DEFAULT, CRYPTO_NETWORK, CACHE_TTL

# ========== НАСТРОЙКА SQLite ==========
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    try:
        if isinstance(s, bytes):
            s = s.decode()
        return datetime.fromisoformat(s)
    except:
        return datetime.now()

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# ========== КЭШ ==========
cache = {"user": {}, "top": {}, "stats": {}, "settings": {}}

def get_cached(key: str, cache_dict: dict, ttl: int = CACHE_TTL):
    if key in cache_dict:
        data = cache_dict[key]
        if time.time() < data["expires"]:
            return data["data"]
        else:
            del cache_dict[key]
    return None

def set_cached(key: str, value: Any, cache_dict: dict, ttl: int = CACHE_TTL):
    cache_dict[key] = {"data": value, "expires": time.time() + ttl}

def clear_cache():
    for c in cache.values():
        c.clear()

# ========== БАЗА ДАННЫХ ==========
class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.transaction_lock = asyncio.Lock()
    
    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(
                DATABASE_PATH, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, 
                timeout=10, 
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA synchronous = NORMAL")
            self.cursor.execute("PRAGMA journal_mode = WAL")
            self.cursor.execute("PRAGMA cache_size = 10000")
            self.cursor.execute("PRAGMA temp_store = MEMORY")
        return self
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def init_db(self):
        with self:
            # Пользователи
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (user_id INTEGER PRIMARY KEY, 
                 username TEXT, 
                 first_name TEXT, 
                 balance REAL DEFAULT 0,
                 total_bets REAL DEFAULT 0, 
                 total_games INTEGER DEFAULT 0, 
                 total_wins INTEGER DEFAULT 0,
                 total_win_amount REAL DEFAULT 0, 
                 max_win_streak INTEGER DEFAULT 0,
                 current_win_streak INTEGER DEFAULT 0, 
                 today_bets REAL DEFAULT 0,
                 last_bet_date DATE, 
                 registered_date TIMESTAMP, 
                 favorite_game TEXT,
                 is_banned INTEGER DEFAULT 0, 
                 ban_reason TEXT, 
                 referrer_id INTEGER)''')
            
            # Индексы для быстрого поиска
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_total_bets ON users(total_bets)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_total_win_amount ON users(total_win_amount)")
            
            # Баны
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS bans
                (user_id INTEGER PRIMARY KEY, 
                 reason TEXT, 
                 banned_by INTEGER, 
                 banned_at TIMESTAMP)''')
            
            # Транзакции
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 user_id INTEGER, 
                 type TEXT, 
                 amount REAL,
                 fee REAL DEFAULT 0, 
                 status TEXT, 
                 invoice_id INTEGER UNIQUE, 
                 invoice_url TEXT,
                 transfer_id TEXT UNIQUE, 
                 admin_id INTEGER, 
                 created_at TIMESTAMP)''')
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)")
            
            # Игры
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS games
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 user_id INTEGER, 
                 game_type TEXT, 
                 bet REAL,
                 result INTEGER, 
                 win_amount REAL, 
                 multiplier REAL, 
                 created_at TIMESTAMP)''')
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_user_id ON games(user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at)")
            
            # PvP игры
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS pvp_games
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 chat_id INTEGER, 
                 creator_id INTEGER,
                 opponent_id INTEGER, 
                 game_type TEXT, 
                 bet REAL, 
                 creator_result INTEGER,
                 opponent_result INTEGER, 
                 winner_id INTEGER, 
                 win_amount REAL, 
                 created_at TIMESTAMP)''')
            
            # PvP статистика
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS pvp_stats
                (user_id INTEGER PRIMARY KEY, 
                 total_pvp_games INTEGER DEFAULT 0,
                 total_pvp_wins INTEGER DEFAULT 0, 
                 total_pvp_win_amount REAL DEFAULT 0,
                 FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
            
            # Промокоды
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS promocodes
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 code TEXT UNIQUE, 
                 amount REAL,
                 max_uses INTEGER, 
                 used_count INTEGER DEFAULT 0, 
                 created_by INTEGER,
                 expires_at TIMESTAMP, 
                 is_active INTEGER DEFAULT 1, 
                 created_at TIMESTAMP)''')
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_promocodes_code ON promocodes(code)")
            
            # Использованные промокоды
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS promocode_uses
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 promocode_id INTEGER,
                 user_id INTEGER, 
                 used_at TIMESTAMP)''')
            
            # Статистика проекта
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS project_stats
                (id INTEGER PRIMARY KEY, 
                 total_turnover REAL DEFAULT 0, 
                 total_games INTEGER DEFAULT 0,
                 total_payouts REAL DEFAULT 0, 
                 total_players INTEGER DEFAULT 0,
                 total_deposits REAL DEFAULT 0, 
                 total_withdrawals REAL DEFAULT 0,
                 total_pvp_games INTEGER DEFAULT 0, 
                 created_date DATE)''')
            
            # Настройки
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                (key TEXT PRIMARY KEY, 
                 value TEXT)''')
            
            # Эмодзи игр
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS game_emojis
                (game_num INTEGER PRIMARY KEY, 
                 emoji TEXT NOT NULL)''')
            
            # Инициализация настроек по умолчанию
            settings = [
                ('games_enabled', '1'), 
                ('crypto_network', CRYPTO_NETWORK),
                ('min_bet', str(MIN_BET_DEFAULT)), 
                ('min_deposit', str(MIN_DEPOSIT_DEFAULT)),
                ('min_withdraw', str(MIN_WITHDRAW_DEFAULT)), 
                ('pvp_multiplier', str(PVP_MULTIPLIER_DEFAULT)),
                ('withdraw_fee', '0.1')  # 10% комиссия по умолчанию
            ]
            for key, value in settings:
                self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            # Инициализация коэффициентов для каждой игры
            for game_key, game_data in GAME_RULES.items():
                if isinstance(game_data["multiplier"], (int, float)):
                    multiplier_value = str(game_data["multiplier"])
                else:
                    multiplier_value = str(max(game_data["multiplier"].values()))
                self.cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                    (f"game_multiplier_{game_key}", multiplier_value)
                )
            
            self.cursor.execute("INSERT OR IGNORE INTO project_stats (id) VALUES (1)")
            
            # Стандартные эмодзи для игр
            for i, (key, game) in enumerate(GAME_RULES.items()):
                self.cursor.execute(
                    "INSERT OR IGNORE INTO game_emojis (game_num, emoji) VALUES (?, ?)",
                    (i, game["emoji"])
                )
            
            # Проверяем наличие нужных колонок и добавляем если отсутствуют
            self.cursor.execute("PRAGMA table_info(project_stats)")
            columns = [col[1] for col in self.cursor.fetchall()]
            if 'total_pvp_games' not in columns:
                self.cursor.execute("ALTER TABLE project_stats ADD COLUMN total_pvp_games INTEGER DEFAULT 0")
            
            self.cursor.execute("PRAGMA table_info(transactions)")
            columns = [col[1] for col in self.cursor.fetchall()]
            if 'fee' not in columns:
                self.cursor.execute("ALTER TABLE transactions ADD COLUMN fee REAL DEFAULT 0")
            
            self.conn.commit()
        print("✅ Database initialized")
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    def get_user(self, user_id: int):
        cached = get_cached(f"user_{user_id}", cache["user"])
        if cached:
            return cached
        with self:
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = self.cursor.fetchone()
            result = dict(user) if user else None
            if result:
                set_cached(f"user_{user_id}", result, cache["user"])
            return result
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, referrer_id: int = None):
        with self:
            # Проверяем, существует ли уже пользователь
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            if self.cursor.fetchone():
                return  # Пользователь уже существует
            
            self.cursor.execute("""INSERT INTO users 
                (user_id, username, first_name, registered_date, referrer_id)
                VALUES (?, ?, ?, ?, ?)""", 
                (user_id, username, first_name, datetime.now(), referrer_id))
            
            # Создаем запись в pvp_stats
            self.cursor.execute("INSERT OR IGNORE INTO pvp_stats (user_id) VALUES (?)", (user_id,))
            
            self.cursor.execute("UPDATE project_stats SET total_players = total_players + 1 WHERE id = 1")
            self.conn.commit()
            
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            
            print(f"👤 New user registered: {user_id}")
    
    async def update_balance(self, user_id: int, amount: float, admin_id: int = None):
        async with self.transaction_lock:
            with self:
                self.cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
                result = self.cursor.fetchone()
                current_balance = float(result[0]) if result else 0.0
                
                if amount < 0 and current_balance < abs(amount):
                    return False
                
                new_balance = current_balance + amount
                self.cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
                
                if admin_id:
                    trans_type = "admin_add" if amount > 0 else "admin_remove"
                    self.cursor.execute("""INSERT INTO transactions 
                        (user_id, type, amount, status, admin_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)""", 
                        (user_id, trans_type, abs(amount), 'completed', admin_id, datetime.now()))
                
                self.conn.commit()
                
                if f"user_{user_id}" in cache["user"]:
                    del cache["user"][f"user_{user_id}"]
                
                return True
    
    def get_balance(self, user_id: int) -> float:
        user = self.get_user(user_id)
        return user['balance'] if user else 0.0
    
    def is_banned(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user and user['is_banned'] == 1
    
    # ========== СТАТИСТИКА ИГР ==========
    def update_game_stats(self, user_id: int, bet: float, win_amount: float, game_type: str):
        with self:
            won = win_amount > 0
            self.cursor.execute("""UPDATE users SET 
                total_games = total_games + 1, 
                total_bets = total_bets + ?,
                total_wins = total_wins + ?, 
                total_win_amount = total_win_amount + ?,
                favorite_game = COALESCE(?, favorite_game) 
                WHERE user_id = ?""",
                (bet, 1 if won else 0, win_amount, game_type, user_id))
            
            self.cursor.execute("""UPDATE project_stats SET 
                total_turnover = total_turnover + ?,
                total_games = total_games + 1, 
                total_payouts = total_payouts + ? 
                WHERE id = 1""", (bet, win_amount))
            
            self.conn.commit()
            
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            cache["top"].clear()
            cache["stats"].clear()
    
    def save_game(self, user_id: int, game_type: str, bet: float, result: int, win_amount: float, multiplier: float):
        with self:
            self.cursor.execute("""INSERT INTO games 
                (user_id, game_type, bet, result, win_amount, multiplier, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (user_id, game_type, bet, result, win_amount, multiplier, datetime.now()))
            self.conn.commit()
    
    # ========== PVP СТАТИСТИКА ==========
    def update_pvp_stats(self, user_id: int, won: bool, win_amount: float):
        with self:
            # Проверяем есть ли запись
            self.cursor.execute("SELECT * FROM pvp_stats WHERE user_id = ?", (user_id,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO pvp_stats (user_id) VALUES (?)", (user_id,))
            
            self.cursor.execute("""UPDATE pvp_stats SET 
                total_pvp_games = total_pvp_games + 1,
                total_pvp_wins = total_pvp_wins + ?, 
                total_pvp_win_amount = total_pvp_win_amount + ?
                WHERE user_id = ?""",
                (1 if won else 0, win_amount, user_id))
            
            self.cursor.execute("UPDATE project_stats SET total_pvp_games = total_pvp_games + 1 WHERE id = 1")
            self.conn.commit()
            
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            cache["top"].clear()
    
    def get_pvp_stats(self, user_id: int):
        cached = get_cached(f"pvp_{user_id}", cache["stats"])
        if cached:
            return cached
        with self:
            self.cursor.execute("SELECT * FROM pvp_stats WHERE user_id = ?", (user_id,))
            stats = self.cursor.fetchone()
            result = dict(stats) if stats else {"total_pvp_games": 0, "total_pvp_wins": 0, "total_pvp_win_amount": 0}
            set_cached(f"pvp_{user_id}", result, cache["stats"])
            return result
    
    def save_pvp_game(self, chat_id: int, creator_id: int, opponent_id: int, game_type: str, 
                      bet: float, creator_result: int, opponent_result: int, winner_id: int, win_amount: float):
        with self:
            self.cursor.execute("""INSERT INTO pvp_games 
                (chat_id, creator_id, opponent_id, game_type, bet,
                 creator_result, opponent_result, winner_id, win_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chat_id, creator_id, opponent_id, game_type, bet, 
                 creator_result, opponent_result, winner_id, win_amount, datetime.now()))
            self.conn.commit()
    
    # ========== БАНЫ ==========
    def ban_user(self, user_id: int, reason: str, admin_id: int):
        with self:
            self.cursor.execute("""INSERT OR REPLACE INTO bans 
                (user_id, reason, banned_by, banned_at) VALUES (?, ?, ?, ?)""",
                (user_id, reason, admin_id, datetime.now()))
            self.cursor.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", (reason, user_id))
            self.conn.commit()
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
    
    def unban_user(self, user_id: int):
        with self:
            self.cursor.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
            self.cursor.execute("UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?", (user_id,))
            self.conn.commit()
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
    
    def get_banned_users(self):
        with self:
            self.cursor.execute("SELECT * FROM bans ORDER BY banned_at DESC")
            return self.cursor.fetchall()
    
    # ========== ПРОМОКОДЫ ==========
    def create_promocode(self, code: str, amount: float, max_uses: int, created_by: int, expires_days: int = 30):
        expires_at = datetime.now() + timedelta(days=expires_days)
        with self:
            try:
                self.cursor.execute("""INSERT INTO promocodes 
                    (code, amount, max_uses, created_by, expires_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""", 
                    (code.upper(), amount, max_uses, created_by, expires_at, datetime.now()))
                self.conn.commit()
                return self.cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    
    def use_promocode(self, code: str, user_id: int) -> Optional[float]:
        with self:
            # Ищем активный промокод
            self.cursor.execute("""SELECT * FROM promocodes 
                WHERE code = ? AND is_active = 1 AND used_count < max_uses
                AND (expires_at IS NULL OR expires_at > ?)""", 
                (code.upper(), datetime.now()))
            promocode = self.cursor.fetchone()
            
            if not promocode:
                return None
            
            # Проверяем, не использовал ли пользователь этот промокод
            self.cursor.execute("""SELECT id FROM promocode_uses 
                WHERE promocode_id = ? AND user_id = ?""", (promocode['id'], user_id))
            if self.cursor.fetchone():
                return None
            
            # Обновляем счетчик использований
            self.cursor.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE id = ?", (promocode['id'],))
            
            # Записываем использование
            self.cursor.execute("INSERT INTO promocode_uses (promocode_id, user_id, used_at) VALUES (?, ?, ?)",
                              (promocode['id'], user_id, datetime.now()))
            
            # Начисляем бонус
            self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (promocode['amount'], user_id))
            
            self.conn.commit()
            
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            
            return promocode['amount']
    
    def get_all_promocodes(self):
        with self:
            self.cursor.execute("""SELECT p.*, COUNT(pu.id) as actual_uses 
                FROM promocodes p
                LEFT JOIN promocode_uses pu ON p.id = pu.promocode_id 
                GROUP BY p.id 
                ORDER BY p.created_at DESC""")
            return self.cursor.fetchall()
    
    # ========== ТРАНЗАКЦИИ ==========
    async def save_transaction(self, user_id: int, type_: str, amount: float, status: str,
                        invoice_id: int = None, invoice_url: str = None, transfer_id: str = None, 
                        admin_id: int = None, fee: float = 0):
        async with self.transaction_lock:
            with self:
                try:
                    self.cursor.execute("""INSERT INTO transactions 
                        (user_id, type, amount, fee, status,
                         invoice_id, invoice_url, transfer_id, admin_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, type_, amount, fee, status, 
                         invoice_id, invoice_url, transfer_id, admin_id, datetime.now()))
                    self.conn.commit()
                    
                    if type_ == 'deposit' and status == 'completed':
                        self.cursor.execute("UPDATE project_stats SET total_deposits = total_deposits + ? WHERE id = 1", (amount,))
                    elif type_ == 'withdraw' and status == 'completed':
                        self.cursor.execute("UPDATE project_stats SET total_withdrawals = total_withdrawals + ? WHERE id = 1", (amount,))
                    
                    self.conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    print(f"⚠️ Duplicate transaction detected")
                    return False
    
    # ========== СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ ==========
    def get_user_stats_full(self, user_id: int) -> Dict:
        cached = get_cached(f"full_stats_{user_id}", cache["stats"])
        if cached:
            return cached
        with self:
            self.cursor.execute("""SELECT u.*, p.total_pvp_games, p.total_pvp_wins, p.total_pvp_win_amount
                FROM users u 
                LEFT JOIN pvp_stats p ON u.user_id = p.user_id 
                WHERE u.user_id = ?""", (user_id,))
            result = self.cursor.fetchone()
            result_dict = dict(result) if result else {}
            set_cached(f"full_stats_{user_id}", result_dict, cache["stats"])
            return result_dict
    
    def update_user_stat(self, user_id: int, field: str, value: float) -> bool:
        allowed_fields = ['balance', 'total_bets', 'total_games', 'total_wins', 
                          'total_win_amount', 'max_win_streak', 'current_win_streak', 'today_bets']
        if field not in allowed_fields:
            return False
        with self:
            self.cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            self.conn.commit()
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            if f"full_stats_{user_id}" in cache["stats"]:
                del cache["stats"][f"full_stats_{user_id}"]
            cache["top"].clear()
            return True
    
    def update_pvp_stat(self, user_id: int, field: str, value: float) -> bool:
        allowed_fields = ['total_pvp_games', 'total_pvp_wins', 'total_pvp_win_amount']
        if field not in allowed_fields:
            return False
        with self:
            # Проверяем есть ли запись
            self.cursor.execute("SELECT * FROM pvp_stats WHERE user_id = ?", (user_id,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO pvp_stats (user_id) VALUES (?)", (user_id,))
            
            self.cursor.execute(f"UPDATE pvp_stats SET {field} = ? WHERE user_id = ?", (value, user_id))
            self.conn.commit()
            if f"pvp_{user_id}" in cache["stats"]:
                del cache["stats"][f"pvp_{user_id}"]
            if f"full_stats_{user_id}" in cache["stats"]:
                del cache["stats"][f"full_stats_{user_id}"]
            cache["top"].clear()
            return True
    
    def reset_user_stats(self, user_id: int) -> bool:
        with self:
            self.cursor.execute("""UPDATE users SET 
                total_bets = 0, 
                total_games = 0, 
                total_wins = 0,
                total_win_amount = 0, 
                max_win_streak = 0, 
                current_win_streak = 0, 
                today_bets = 0 
                WHERE user_id = ?""", (user_id,))
            
            self.cursor.execute("""UPDATE pvp_stats SET 
                total_pvp_games = 0, 
                total_pvp_wins = 0,
                total_pvp_win_amount = 0 
                WHERE user_id = ?""", (user_id,))
            
            self.conn.commit()
            
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            if f"pvp_{user_id}" in cache["stats"]:
                del cache["stats"][f"pvp_{user_id}"]
            if f"full_stats_{user_id}" in cache["stats"]:
                del cache["stats"][f"full_stats_{user_id}"]
            cache["top"].clear()
            return True
    
    def reset_all_stats(self) -> bool:
        with self:
            # Сброс статистики пользователей
            self.cursor.execute("""UPDATE users SET 
                total_bets = 0, 
                total_games = 0, 
                total_wins = 0,
                total_win_amount = 0, 
                max_win_streak = 0, 
                current_win_streak = 0, 
                today_bets = 0""")
            
            # Сброс PvP статистики
            self.cursor.execute("""UPDATE pvp_stats SET 
                total_pvp_games = 0, 
                total_pvp_wins = 0, 
                total_pvp_win_amount = 0""")
            
            # Сброс статистики проекта
            self.cursor.execute("""UPDATE project_stats SET 
                total_turnover = 0, 
                total_games = 0,
                total_payouts = 0, 
                total_pvp_games = 0 
                WHERE id = 1""")
            
            self.conn.commit()
            clear_cache()
            return True
    
    # ========== ТОП ИГРОКОВ ==========
    def get_top_players_custom(self, field: str, limit: int = 10):
        cache_key = f"top_{field}_{limit}"
        cached = get_cached(cache_key, cache["top"])
        if cached:
            return cached
        
        allowed_fields = {
            'total_win_amount': '💰 По выигрышам', 
            'total_bets': '💸 По обороту',
            'total_games': '🎮 По количеству игр', 
            'total_wins': '✅ По победам',
            'balance': '💎 По балансу'
        }
        if field not in allowed_fields:
            field = 'total_win_amount'
        
        with self:
            self.cursor.execute(f"""SELECT user_id, username, first_name, {field} as value
                FROM users 
                WHERE {field} > 0 
                ORDER BY {field} DESC 
                LIMIT ?""", (limit,))
            result = (self.cursor.fetchall(), allowed_fields.get(field, field))
            set_cached(cache_key, result, cache["top"])
            return result
    
    def get_top_pvp_custom(self, field: str, limit: int = 10):
        cache_key = f"top_pvp_{field}_{limit}"
        cached = get_cached(cache_key, cache["top"])
        if cached:
            return cached
        
        allowed_fields = {
            'total_pvp_win_amount': '💰 По выигрышам в PvP',
            'total_pvp_games': '🎮 По количеству PvP игр',
            'total_pvp_wins': '✅ По победам в PvP'
        }
        if field not in allowed_fields:
            field = 'total_pvp_win_amount'
        
        with self:
            self.cursor.execute(f"""SELECT u.user_id, u.username, u.first_name, p.{field} as value
                FROM pvp_stats p 
                JOIN users u ON u.user_id = p.user_id
                WHERE p.{field} > 0 
                ORDER BY p.{field} DESC 
                LIMIT ?""", (limit,))
            result = (self.cursor.fetchall(), allowed_fields.get(field, field))
            set_cached(cache_key, result, cache["top"])
            return result
    
    def get_top_players(self, limit: int = 10):
        return self.get_top_players_custom('total_win_amount', limit)
    
    def get_top_pvp_players(self, limit: int = 10):
        return self.get_top_pvp_custom('total_pvp_win_amount', limit)
    
    def set_top_position(self, user_id: int, position: int, field: str, value: float) -> bool:
        allowed_fields = ['total_win_amount', 'total_bets', 'total_games', 'total_wins', 'balance']
        if field not in allowed_fields:
            return False
        with self:
            # Получаем текущее значение у пользователя на этой позиции
            self.cursor.execute(f"""SELECT user_id, {field} FROM users 
                WHERE {field} > 0 
                ORDER BY {field} DESC 
                LIMIT 1 OFFSET ?""", (position - 1,))
            current = self.cursor.fetchone()
            
            if current:
                current_user_id, current_value = current
                # Меняем значения местами
                self.cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
                self.cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (current_value, current_user_id))
            else:
                # Просто устанавливаем значение
                self.cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            
            self.conn.commit()
            cache["top"].clear()
            if f"user_{user_id}" in cache["user"]:
                del cache["user"][f"user_{user_id}"]
            if current and f"user_{current_user_id}" in cache["user"]:
                del cache["user"][f"user_{current_user_id}"]
            return True
    
    # ========== СТАТИСТИКА ПРОЕКТА ==========
    def get_project_stats(self):
        cache_key = "project_stats"
        cached = get_cached(cache_key, cache["stats"])
        if cached:
            return cached
        with self:
            self.cursor.execute("SELECT * FROM project_stats WHERE id = 1")
            stats = self.cursor.fetchone()
            result = dict(stats) if stats else {}
            set_cached(cache_key, result, cache["stats"])
            return result
    
    def get_all_users_count(self):
        cache_key = "users_count"
        cached = get_cached(cache_key, cache["stats"])
        if cached:
            return cached
        with self:
            self.cursor.execute("SELECT COUNT(*) FROM users")
            result = self.cursor.fetchone()[0]
            set_cached(cache_key, result, cache["stats"])
            return result
    
    def get_active_users_count(self, days: int = 7):
        cache_key = f"active_users_{days}"
        cached = get_cached(cache_key, cache["stats"])
        if cached:
            return cached
        since = datetime.now() - timedelta(days=days)
        with self:
            self.cursor.execute("SELECT COUNT(DISTINCT user_id) FROM games WHERE created_at > ?", (since.isoformat(),))
            result = self.cursor.fetchone()[0]
            set_cached(cache_key, result, cache["stats"])
            return result
    
    def get_all_users_for_mailing(self):
        with self:
            self.cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
            return [row[0] for row in self.cursor.fetchall()]
    
    # ========== ПОИСК ПОЛЬЗОВАТЕЛЕЙ ==========
    def search_users_paginated(self, query: str, page: int = 1, limit: int = 10):
        offset = (page - 1) * limit
        with self:
            # Общее количество
            self.cursor.execute("""SELECT COUNT(*) FROM users 
                WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ?""",
                (f'%{query}%', f'%{query}%', f'%{query}%'))
            total = self.cursor.fetchone()[0]
            
            # Пользователи для текущей страницы
            self.cursor.execute("""SELECT * FROM users 
                WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ?
                ORDER BY total_bets DESC 
                LIMIT ? OFFSET ?""",
                (f'%{query}%', f'%{query}%', f'%{query}%', limit, offset))
            users = self.cursor.fetchall()
            
            return users, total
    
    def get_all_users_paginated(self, page: int = 1, limit: int = 10):
        offset = (page - 1) * limit
        with self:
            # Общее количество
            self.cursor.execute("SELECT COUNT(*) FROM users")
            total = self.cursor.fetchone()[0]
            
            # Пользователи для текущей страницы
            self.cursor.execute("SELECT * FROM users ORDER BY total_bets DESC LIMIT ? OFFSET ?", (limit, offset))
            users = self.cursor.fetchall()
            
            return users, total
    
    # ========== НАСТРОЙКИ ==========
    def get_setting(self, key: str, default=None):
        cache_key = f"setting_{key}"
        cached = get_cached(cache_key, cache["settings"])
        if cached is not None:
            return cached
        with self:
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            value = result[0] if result else default
            set_cached(cache_key, value, cache["settings"])
            return value
    
    def set_setting(self, key: str, value: str):
        with self:
            self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
            if f"setting_{key}" in cache["settings"]:
                del cache["settings"][f"setting_{key}"]
    
    def are_games_enabled(self) -> bool:
        return self.get_setting('games_enabled', '1') == '1'
    
    def toggle_games(self, enabled: bool):
        self.set_setting('games_enabled', '1' if enabled else '0')
    
    def get_network(self) -> str:
        return self.get_setting('crypto_network', 'mainnet')
    
    def set_network(self, network: str):
        self.set_setting('crypto_network', network)
    
    def get_min_bet(self) -> float:
        return float(self.get_setting('min_bet', str(MIN_BET_DEFAULT)))
    
    def set_min_bet(self, value: float):
        self.set_setting('min_bet', str(value))
    
    def get_min_deposit(self) -> float:
        return float(self.get_setting('min_deposit', str(MIN_DEPOSIT_DEFAULT)))
    
    def set_min_deposit(self, value: float):
        self.set_setting('min_deposit', str(value))
    
    def get_min_withdraw(self) -> float:
        return float(self.get_setting('min_withdraw', str(MIN_WITHDRAW_DEFAULT)))
    
    def set_min_withdraw(self, value: float):
        self.set_setting('min_withdraw', str(value))
    
    def get_withdraw_fee(self) -> float:
        """Получение комиссии на вывод (в десятичном виде, например 0.1 = 10%)"""
        return float(self.get_setting('withdraw_fee', '0.1'))
    
    def set_withdraw_fee(self, value: float):
        """Установка комиссии на вывод (в десятичном виде)"""
        self.set_setting('withdraw_fee', str(value))
    
    def get_pvp_multiplier(self) -> float:
        return float(self.get_setting('pvp_multiplier', str(PVP_MULTIPLIER_DEFAULT)))
    
    def set_pvp_multiplier(self, value: float):
        self.set_setting('pvp_multiplier', str(value))
    
    def get_game_multiplier(self, game_key: str) -> float:
        return float(self.get_setting(f"game_multiplier_{game_key}", "1.0"))
    
    def set_game_multiplier(self, game_key: str, value: float):
        self.set_setting(f"game_multiplier_{game_key}", str(value))
    
    # ========== ЭМОДЗИ ИГР ==========
    def get_game_emoji(self, game_num: int) -> str:
        with self:
            self.cursor.execute("SELECT emoji FROM game_emojis WHERE game_num = ?", (game_num,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            return list(GAME_RULES.values())[game_num]["emoji"]
    
    def set_game_emoji(self, game_num: int, emoji: str):
        with self:
            self.cursor.execute("UPDATE game_emojis SET emoji = ? WHERE game_num = ?", (emoji, game_num))
            self.conn.commit()
    
    def get_game_by_emoji(self, emoji: str) -> Optional[str]:
        with self:
            self.cursor.execute("SELECT game_num FROM game_emojis WHERE emoji = ?", (emoji,))
            result = self.cursor.fetchone()
            if result:
                game_num = result[0]
                return list(GAME_RULES.keys())[game_num]
            return None

# Глобальный экземпляр базы данных
db = Database()
db.init_db()