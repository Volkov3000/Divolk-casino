# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database import db

def get_main_keyboard(is_admin_user: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🎮 ИГРАТЬ"), KeyboardButton(text="👤 ПРОФИЛЬ"))
    builder.row(KeyboardButton(text="📥 ДЕПОЗИТ"), KeyboardButton(text="📤 ВЫВОД"))
    builder.row(KeyboardButton(text="ℹ️ О ПРОЕКТЕ"), KeyboardButton(text="🏆 ТОП"))
    if is_admin_user:
        builder.row(KeyboardButton(text="👑 АДМИН"))
    return builder.as_markup(resize_keyboard=True)

def get_games_keyboard():
    builder = ReplyKeyboardBuilder()
    emoji0, emoji1, emoji2, emoji3, emoji4, emoji5 = [db.get_game_emoji(i) for i in range(6)]
    builder.row(
        KeyboardButton(text=f"{emoji0} СЛОТЫ"),
        KeyboardButton(text=f"{emoji1} БОУЛИНГ"),
        KeyboardButton(text=f"{emoji2} ФУТБОЛ")
    )
    builder.row(
        KeyboardButton(text=f"{emoji3} БАСКЕТ"),
        KeyboardButton(text=f"{emoji4} ДАРТС"),
        KeyboardButton(text=f"{emoji5} КУБИК")
    )
    builder.row(KeyboardButton(text="◀️ НАЗАД"))
    return builder.as_markup(resize_keyboard=True)

def get_profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 ОБНОВИТЬ", callback_data="profile_refresh"),
        InlineKeyboardButton(text="🎟 ПРОМОКОД", callback_data="profile_promo")
    )
    builder.row(
        InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="profile_stats"),
        InlineKeyboardButton(text="⚔️ PVP", callback_data="profile_pvp")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="profile_main")
    )
    return builder.as_markup()

def get_stats_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 ОБНОВИТЬ", callback_data="stats_refresh"),
        InlineKeyboardButton(text="🏆 ТОП", callback_data="stats_top")
    )
    builder.row(
        InlineKeyboardButton(text="⚔️ ТОП PVP", callback_data="stats_pvp_top"),
        InlineKeyboardButton(text="👤 ПРОФИЛЬ", callback_data="stats_profile")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="stats_main")
    )
    return builder.as_markup()

def get_top_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 ОБНОВИТЬ", callback_data="top_refresh"),
        InlineKeyboardButton(text="👤 ПРОФИЛЬ", callback_data="top_profile")
    )
    builder.row(
        InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="top_stats"),
        InlineKeyboardButton(text="⚔️ PVP", callback_data="top_pvp")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="top_main")
    )
    return builder.as_markup()

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    buttons = [
        ("👥 ПОИСК", "admin_user_search"),
        ("💰 БАЛАНС", "admin_balance_menu"),
        ("🚫 БАНЫ", "admin_ban_menu"),
        ("🎟 ПРОМОКОДЫ", "admin_promo_menu"),
        ("🎮 ИГРЫ", "admin_games_menu"),
        ("⚙️ НАСТРОЙКИ", "admin_settings_menu"),
        ("📊 СТАТИСТИКА", "admin_stats_management"),
        ("📊 SERVER STAT", "admin_server_stats"),
        ("⏸ СТОП-ИГРЫ", "admin_toggle_games"),
        ("🌐 СЕТЬ", "admin_network_menu"),
        ("📢 РАССЫЛКА", "admin_mailing")
    ]
    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)
    builder.button(text="◀️ ЗАКРЫТЬ", callback_data="admin_close")
    builder.adjust(2)
    return builder.as_markup()

def get_balance_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ ДОБАВИТЬ", callback_data="admin_balance_add"),
        InlineKeyboardButton(text="➖ ЗАБРАТЬ", callback_data="admin_balance_remove")
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
    return builder.as_markup()

def get_ban_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚫 ЗАБАНИТЬ", callback_data="admin_ban_ban"),
        InlineKeyboardButton(text="✅ РАЗБАНИТЬ", callback_data="admin_ban_unban")
    )
    builder.row(
        InlineKeyboardButton(text="📋 СПИСОК", callback_data="admin_ban_list"),
        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main")
    )
    return builder.as_markup()

def get_promo_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎟 СОЗДАТЬ", callback_data="admin_promo_create"),
        InlineKeyboardButton(text="📋 СПИСОК", callback_data="admin_promo_list")
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
    return builder.as_markup()

def get_games_admin_keyboard():
    builder = InlineKeyboardBuilder()
    emoji0, emoji1, emoji2, emoji3, emoji4, emoji5 = [db.get_game_emoji(i) for i in range(6)]
    builder.row(
        InlineKeyboardButton(text=f"{emoji0} СЛОТЫ", callback_data="admin_game_0"),
        InlineKeyboardButton(text=f"{emoji1} БОУЛИНГ", callback_data="admin_game_1"),
        InlineKeyboardButton(text=f"{emoji2} ФУТБОЛ", callback_data="admin_game_2")
    )
    builder.row(
        InlineKeyboardButton(text=f"{emoji3} БАСКЕТ", callback_data="admin_game_3"),
        InlineKeyboardButton(text=f"{emoji4} ДАРТС", callback_data="admin_game_4"),
        InlineKeyboardButton(text=f"{emoji5} КУБИК", callback_data="admin_game_5")
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
    return builder.as_markup()

def get_settings_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Мин. ставка", callback_data="admin_settings_min_bet"),
        InlineKeyboardButton(text="📥 Мин. депозит", callback_data="admin_settings_min_deposit")
    )
    builder.row(
        InlineKeyboardButton(text="📤 Мин. вывод", callback_data="admin_settings_min_withdraw"),
        InlineKeyboardButton(text="💸 Комиссия вывода", callback_data="admin_settings_withdraw_fee")
    )
    builder.row(
        InlineKeyboardButton(text="⚔️ PvP множитель", callback_data="admin_settings_pvp_multiplier"),
        InlineKeyboardButton(text="🎲 Коэф. игр", callback_data="admin_settings_game_multipliers")
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
    builder.adjust(2)
    return builder.as_markup()

def get_game_multipliers_keyboard():
    builder = InlineKeyboardBuilder()
    emoji0, emoji1, emoji2, emoji3, emoji4, emoji5 = [db.get_game_emoji(i) for i in range(6)]
    games = [
        (f"{emoji0} СЛОТЫ", "slots"),
        (f"{emoji1} БОУЛИНГ", "bowling"),
        (f"{emoji2} ФУТБОЛ", "football"),
        (f"{emoji3} БАСКЕТ", "basketball"),
        (f"{emoji4} ДАРТС", "darts"),
        (f"{emoji5} КУБИК", "dice")
    ]
    for text, game_key in games:
        current = db.get_game_multiplier(game_key)
        if game_key == "dice":
            builder.button(text=f"{text} (1.4-1.9)", callback_data=f"admin_game_multiplier_{game_key}")
        else:
            builder.button(text=f"{text} (x{current})", callback_data=f"admin_game_multiplier_{game_key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_settings_menu"))
    return builder.as_markup()

def get_network_admin_keyboard(current_network: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅ ' if current_network == 'mainnet' else ''}MAINNET",
            callback_data="admin_network_mainnet"
        ),
        InlineKeyboardButton(
            text=f"{'✅ ' if current_network == 'testnet' else ''}TESTNET",
            callback_data="admin_network_testnet"
        )
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
    return builder.as_markup()

def get_user_action_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 БАЛАНС", callback_data=f"admin_user_balance_{user_id}"),
        InlineKeyboardButton(text="🚫 БАН", callback_data=f"admin_user_ban_{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📨 СООБЩЕНИЕ", callback_data=f"admin_user_message_{user_id}"),
        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main")
    )
    return builder.as_markup()

def get_user_balance_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ ДОБАВИТЬ", callback_data=f"admin_balance_add_{user_id}"),
        InlineKeyboardButton(text="➖ ЗАБРАТЬ", callback_data=f"admin_balance_remove_{user_id}")
    )
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data=f"admin_user_view_{user_id}"))
    return builder.as_markup()

# ========== НОВАЯ ФУНКЦИЯ ==========
def get_game_emoji_keyboard(game_num: int, current_emoji: str):
    """Клавиатура для выбора эмодзи игры"""
    builder = InlineKeyboardBuilder()
    emojis = ["🎰", "🎳", "⚽", "🏀", "🎯", "🎲", "🎮", "🎪", "🎨", "🎭", "🎢", "🎱"]
    
    # Получаем используемые эмодзи
    used_emojis = []
    for i in range(6):
        if i != game_num:
            used_emojis.append(db.get_game_emoji(i))
    
    for emoji in emojis:
        # Проверяем, доступен ли эмодзи (не используется в других играх)
        if emoji in used_emojis and emoji != current_emoji:
            text = f"{emoji} ❌"
            callback_data = "noop"
        else:
            text = f"{emoji} ✅" if emoji == current_emoji else emoji
            callback_data = f"admin_game_emoji_{game_num}_{emoji}"
        
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_games_menu"))
    return builder.as_markup()

def get_pagination_keyboard(base_callback: str, current_page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    if current_page > 1:
        builder.button(text="◀️", callback_data=f"{base_callback}_page_{current_page-1}")
    builder.button(text=f"{current_page}/{total_pages}", callback_data="noop")
    if current_page < total_pages:
        builder.button(text="▶️", callback_data=f"{base_callback}_page_{current_page+1}")
    builder.adjust(3)
    return builder.as_markup()

def get_repeat_keyboard(game_key: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 ПОВТОРИТЬ", callback_data=f"repeat_game_{game_key}")
    return builder.as_markup()

def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ ОТМЕНА"))
    return builder.as_markup(resize_keyboard=True)

def get_stats_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Статистика игрока", callback_data="admin_stats_user"),
        InlineKeyboardButton(text="📊 Топ игроков", callback_data="admin_stats_top")
    )
    builder.row(
        InlineKeyboardButton(text="⚔️ PvP статистика", callback_data="admin_stats_pvp"),
        InlineKeyboardButton(text="🔄 Сброс статистики", callback_data="admin_stats_reset")
    )
    builder.row(
        InlineKeyboardButton(text="📈 Общая статистика", callback_data="admin_stats_project"),
        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main")
    )
    return builder.as_markup()

def get_user_stats_fields_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    fields = [
        ("💰 Баланс", "balance"),
        ("💸 Оборот", "total_bets"),
        ("🎮 Всего игр", "total_games"),
        ("✅ Побед", "total_wins"),
        ("🏆 Выиграно", "total_win_amount"),
        ("📈 Макс. винстрик", "max_win_streak"),
        ("📊 Тек. винстрик", "current_win_streak"),
        ("💎 Ставок сегодня", "today_bets")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"admin_stats_user_field_{user_id}_{field}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_user"))
    return builder.as_markup()

def get_pvp_stats_fields_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    fields = [
        ("🎮 Всего PvP игр", "total_pvp_games"),
        ("✅ Побед в PvP", "total_pvp_wins"),
        ("💰 Выиграно в PvP", "total_pvp_win_amount")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"admin_stats_pvp_field_{user_id}_{field}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_user"))
    return builder.as_markup()

def get_top_fields_keyboard():
    builder = InlineKeyboardBuilder()
    fields = [
        ("💰 По выигрышам", "total_win_amount"),
        ("💸 По обороту", "total_bets"),
        ("🎮 По количеству игр", "total_games"),
        ("✅ По победам", "total_wins"),
        ("💎 По балансу", "balance")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"admin_top_view_{field}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management"))
    return builder.as_markup()

def get_top_pvp_fields_keyboard():
    builder = InlineKeyboardBuilder()
    fields = [
        ("💰 По выигрышам", "total_pvp_win_amount"),
        ("🎮 По количеству игр", "total_pvp_games"),
        ("✅ По победам", "total_pvp_wins")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"admin_top_pvp_view_{field}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management"))
    return builder.as_markup()

def get_top_actions_keyboard(field: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить позицию", callback_data=f"admin_top_edit_{field}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin_top_refresh_{field}")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Другой топ", callback_data="admin_stats_top"),
        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management")
    )
    return builder.as_markup()

def get_top_pvp_actions_keyboard(field: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить позицию", callback_data=f"admin_top_pvp_edit_{field}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"admin_top_pvp_refresh_{field}")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Другой топ", callback_data="admin_stats_pvp"),
        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management")
    )
    return builder.as_markup()

def get_reset_stats_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ ДА, СБРОСИТЬ ВСЁ", callback_data="admin_stats_reset_confirm"),
        InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="admin_stats_management")
    )
    return builder.as_markup()

def get_balance_amount_keyboard(action: str, user_id: int):
    builder = InlineKeyboardBuilder()
    amounts = [1, 5, 10, 50, 100]
    for amount in amounts:
        builder.button(text=f"${amount}", callback_data=f"admin_balance_{action}_{user_id}_{amount}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data=f"admin_user_balance_{user_id}"))
    return builder.as_markup()

def get_promo_amount_keyboard():
    builder = InlineKeyboardBuilder()
    amounts = [1, 5, 10, 50, 100]
    for amount in amounts:
        builder.button(text=f"${amount}", callback_data=f"admin_promo_amount_{amount}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_promo_create"))
    return builder.as_markup()

def get_promo_uses_keyboard():
    builder = InlineKeyboardBuilder()
    uses = [1, 5, 10, 50, 100]
    for use in uses:
        builder.button(text=str(use), callback_data=f"admin_promo_uses_{use}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_promo_create"))
    return builder.as_markup()