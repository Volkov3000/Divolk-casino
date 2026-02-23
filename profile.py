# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from utils import get_user_rank, get_vip_progress, pluralize, format_number, is_admin, crypto, log_deposit, log_withdraw
from keyboards import get_profile_keyboard, get_stats_keyboard, get_top_keyboard, get_cancel_keyboard, get_main_keyboard
from config import GameStates, PromoStates, DISPLAY_TIMEOUT, WITHDRAW_FEE
from datetime import datetime
import asyncio

# ========== ЭКСПОРТИРУЕМЫЕ ФУНКЦИИ ==========

async def profile_menu(message: Message):
    """Профиль пользователя"""
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    user = db.get_user(user_id)
    reg_date = user['registered_date'] if isinstance(user['registered_date'], datetime) else datetime.strptime(user['registered_date'][:10], "%Y-%m-%d")
    days = (datetime.now() - reg_date).days
    rank = get_user_rank(user['total_bets'])
    rank_text, vip_progress = get_vip_progress(user['total_bets'])
    win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
    pvp_stats = db.get_pvp_stats(user_id)
    
    text = f"""
👤 <b>Ваш профиль ›</b>

<blockquote>💰 Баланс — ${user['balance']:.0f}</blockquote>

<blockquote>🏆 Ваш ранг — {rank}</blockquote>
<blockquote>📊 VIP прогресс — {vip_progress:.0f}%</blockquote>
<blockquote>{rank_text}</blockquote>

<blockquote>🪙 Оборот — {format_number(user['total_bets'])}</blockquote>
<blockquote>🎮 Сыграно — {user['total_games']} ставок</blockquote>
<blockquote>⚔️ PvP игр — {pvp_stats['total_pvp_games']}</blockquote>
<blockquote>📈 Винрейт — {win_rate:.1f}%</blockquote>
<blockquote>⏲ Аккаунту — {days} {pluralize(days, 'день', 'дня', 'дней')}</blockquote>
    """
    await message.answer_photo(
        photo=types.FSInputFile("images/profile.png"),
        caption=text,
        reply_markup=get_profile_keyboard()
    )

async def deposit_menu(message: Message, state: FSMContext):
    """Меню депозита"""
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    min_deposit = db.get_min_deposit()
    await message.answer_photo(
        photo=types.FSInputFile("images/deposit.png"),
        caption=f"📥 <b>ДЕПОЗИТ</b>\n\n"
                f"Введи сумму пополнения в USDT (мин. ${min_deposit}):\n\n"
                "<blockquote>Пример: 10, 25.5, 100</blockquote>"
    )
    await state.set_state(GameStates.waiting_for_deposit)

async def withdraw_menu(message: Message):
    """Меню вывода"""
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    user = db.get_user(user_id)
    min_withdraw = db.get_min_withdraw()
    
    if user['balance'] < min_withdraw:
        await message.answer(f"❌ Недостаточно средств для вывода\n\n<blockquote>💰 Баланс: ${user['balance']:.2f}</blockquote>\n<blockquote>📉 Минимум: ${min_withdraw}</blockquote>")
        return
    
    withdraw_amount = user['balance']
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"withdraw_confirm_{int(user['balance'])}")
    
    await message.answer_photo(
        photo=types.FSInputFile("images/withdraw.png"),
        caption=f"📤 <b>ВЫВОД</b>\n\n"
                f"<blockquote>💰 Баланс: ${user['balance']:.2f}</blockquote>\n"
                f"<blockquote>💎 К выводу: ${withdraw_amount:.2f}</blockquote>\n\n"
                f"Подтвердите вывод:",
        reply_markup=builder.as_markup()
    )

async def about_menu(message: Message):
    """Информация о проекте"""
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    stats = db.get_project_stats()
    await message.answer_photo(
        photo=types.FSInputFile("images/stats.png"),
        caption=f"🖲 <b>О ПРОЕКТЕ</b>\n\n"
                f"Каждый ход приближает к победе, если веришь в себя.\n\n"
                f"<b>ℹ️ Информация</b>\n"
                f"<blockquote>📅 Дата основания: 05.02.2025</blockquote>\n"
                f"<blockquote>💰 Оборот: {format_number(stats.get('total_turnover', 0))}</blockquote>\n"
                f"<blockquote>🎮 Обычных игр: {stats.get('total_games', 0)}</blockquote>\n"
                f"<blockquote>⚔️ PvP игр: {stats.get('total_pvp_games', 0)}</blockquote>\n"
                f"<blockquote>💸 Выплат: {format_number(stats.get('total_payouts', 0))}</blockquote>\n"
                f"<blockquote>👥 Игроков: {stats.get('total_players', 0)}</blockquote>"
    )

async def top_menu(message: Message):
    """Топ игроков"""
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    
    players, title = db.get_top_players_custom('total_win_amount', 10)
    text = f"🏆 <b>ТОП-10 ИГРОКОВ</b>\n{title}\n\n"
    
    if players:
        for i, player in enumerate(players, 1):
            name = player['first_name'] or f"Игрок {player['user_id']}"
            if player['username']:
                name = f"@{player['username']}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
            text += f"{medal} {i}. {name}\n"
            text += f"<blockquote>💰 Выиграно: ${player['value']:.0f}</blockquote>\n\n"
    else:
        text += "Пока нет игроков в топе. Стань первым!"
    
    await message.answer_photo(
        photo=types.FSInputFile("images/stats.png"),
        caption=text,
        reply_markup=get_top_keyboard()
    )

# ========== РЕГИСТРАЦИЯ ВСЕХ ОБРАБОТЧИКОВ ==========

def register_profile_handlers(dp):
    @dp.callback_query(lambda c: c.data.startswith('profile_'))
    async def profile_callbacks(callback: CallbackQuery, state: FSMContext):
        action = callback.data.replace('profile_', '')
        
        if action == 'refresh':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            reg_date = user['registered_date'] if isinstance(user['registered_date'], datetime) else datetime.strptime(user['registered_date'][:10], "%Y-%m-%d")
            days = (datetime.now() - reg_date).days
            rank = get_user_rank(user['total_bets'])
            rank_text, vip_progress = get_vip_progress(user['total_bets'])
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            pvp_stats = db.get_pvp_stats(user_id)
            text = f"""
    👤 <b>Ваш профиль › (обновлено)</b>

    <blockquote>💰 Баланс — ${user['balance']:.0f}</blockquote>

    <blockquote>🏆 Ваш ранг — {rank}</blockquote>
    <blockquote>📊 VIP прогресс — {vip_progress:.0f}%</blockquote>
    <blockquote>{rank_text}</blockquote>

    <blockquote>🪙 Оборот — {format_number(user['total_bets'])}</blockquote>
    <blockquote>🎮 Сыграно — {user['total_games']} ставок</blockquote>
    <blockquote>⚔️ PvP игр — {pvp_stats['total_pvp_games']}</blockquote>
    <blockquote>📈 Винрейт — {win_rate:.1f}%</blockquote>
    <blockquote>⏲ Аккаунту — {days} {pluralize(days, 'день', 'дня', 'дней')}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
        
        elif action == 'promo':
            await callback.answer()
            await callback.message.answer("🎟 <b>Активация промокода</b>\n\nВведи код промокода:", reply_markup=get_cancel_keyboard())
            await state.set_state(PromoStates.waiting_for_code)
        
        elif action == 'stats':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            text = f"""
    📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>

    <blockquote>💰 Баланс: ${user['balance']:.0f}</blockquote>
    <blockquote>🪙 Оборот: {format_number(user['total_bets'])}</blockquote>
    <blockquote>🏆 Выиграно: {format_number(user['total_win_amount'])}</blockquote>

    <blockquote>🎮 Сыграно игр: {user['total_games']}</blockquote>
    <blockquote>✅ Побед: {user['total_wins']}</blockquote>
    <blockquote>❌ Поражений: {user['total_games'] - user['total_wins']}</blockquote>

    <blockquote>📈 Макс. винстрик: {user['max_win_streak']}</blockquote>
    <blockquote>📊 Текущий винстрик: {user['current_win_streak']}</blockquote>
    <blockquote>💎 Ставок сегодня: {user['today_bets']:.0f}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
        
        elif action == 'pvp':
            await callback.answer()
            user_id = callback.from_user.id
            pvp_stats = db.get_pvp_stats(user_id)
            win_rate = (pvp_stats['total_pvp_wins'] / pvp_stats['total_pvp_games'] * 100) if pvp_stats['total_pvp_games'] > 0 else 0
            text = f"""
    ⚔️ <b>PVP СТАТИСТИКА</b>

    <blockquote>🎮 Всего PvP игр: {pvp_stats['total_pvp_games']}</blockquote>
    <blockquote>✅ Побед: {pvp_stats['total_pvp_wins']}</blockquote>
    <blockquote>❌ Поражений: {pvp_stats['total_pvp_games'] - pvp_stats['total_pvp_wins']}</blockquote>
    <blockquote>💰 Выиграно: ${pvp_stats['total_pvp_win_amount']:.0f}</blockquote>
    <blockquote>📈 Винрейт: {win_rate:.1f}%</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
        
        elif action == 'main':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            rank = get_user_rank(user['total_bets'])
            await callback.message.edit_text(
                f"🐝 <b>BeeCube</b>\n\n"
                f"👋 Привет, {callback.from_user.first_name}!\n\n"
                f"💰 Баланс — ${user['balance']:.0f}\n"
                f"<blockquote>🏆 Ваш ранг — {rank}</blockquote>",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
    
    @dp.callback_query(lambda c: c.data.startswith('stats_'))
    async def stats_callbacks(callback: CallbackQuery):
        action = callback.data.replace('stats_', '')
        
        if action == 'refresh':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            text = f"""
    📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА (обновлено)</b>

    <blockquote>💰 Баланс: ${user['balance']:.0f}</blockquote>
    <blockquote>🪙 Оборот: {format_number(user['total_bets'])}</blockquote>
    <blockquote>🏆 Выиграно: {format_number(user['total_win_amount'])}</blockquote>

    <blockquote>🎮 Сыграно игр: {user['total_games']}</blockquote>
    <blockquote>✅ Побед: {user['total_wins']}</blockquote>
    <blockquote>❌ Поражений: {user['total_games'] - user['total_wins']}</blockquote>

    <blockquote>📈 Макс. винстрик: {user['max_win_streak']}</blockquote>
    <blockquote>📊 Текущий винстрик: {user['current_win_streak']}</blockquote>
    <blockquote>💎 Ставок сегодня: {user['today_bets']:.0f}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
        
        elif action == 'top':
            await callback.answer()
            players, title = db.get_top_players_custom('total_win_amount', 10)
            text = f"🏆 <b>ТОП-10 ИГРОКОВ</b>\n{title}\n\n"
            if players:
                for i, player in enumerate(players, 1):
                    name = player['first_name'] or f"Игрок {player['user_id']}"
                    if player['username']:
                        name = f"@{player['username']}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
                    text += f"{medal} {i}. {name}\n"
                    text += f"<blockquote>💰 Выиграно: ${player['value']:.0f}</blockquote>\n\n"
            else:
                text += "Пока нет игроков в топе. Стань первым!"
            await callback.message.edit_text(text, reply_markup=get_top_keyboard())
        
        elif action == 'pvp_top':
            await callback.answer()
            players, title = db.get_top_pvp_custom('total_pvp_win_amount', 10)
            text = f"⚔️ <b>ТОП-10 ИГРОКОВ PVP</b>\n{title}\n\n"
            if players:
                for i, player in enumerate(players, 1):
                    name = player['first_name'] or f"Игрок {player['user_id']}"
                    if player['username']:
                        name = f"@{player['username']}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
                    text += f"{medal} {i}. {name}\n"
                    text += f"<blockquote>💰 Выиграно: ${player['value']:.0f}</blockquote>\n"
                    text += f"<blockquote>🎮 Игр: {player['total_pvp_games']}</blockquote>\n\n"
            else:
                text += "Пока нет игроков в топе. Стань первым!"
            await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
        
        elif action == 'profile':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            reg_date = user['registered_date'] if isinstance(user['registered_date'], datetime) else datetime.strptime(user['registered_date'][:10], "%Y-%m-%d")
            days = (datetime.now() - reg_date).days
            rank = get_user_rank(user['total_bets'])
            rank_text, vip_progress = get_vip_progress(user['total_bets'])
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            pvp_stats = db.get_pvp_stats(user_id)
            text = f"""
    👤 <b>Ваш профиль ›</b>

    <blockquote>💰 Баланс — ${user['balance']:.0f}</blockquote>

    <blockquote>🏆 Ваш ранг — {rank}</blockquote>
    <blockquote>📊 VIP прогресс — {vip_progress:.0f}%</blockquote>
    <blockquote>{rank_text}</blockquote>

    <blockquote>🪙 Оборот — {format_number(user['total_bets'])}</blockquote>
    <blockquote>🎮 Сыграно — {user['total_games']} ставок</blockquote>
    <blockquote>⚔️ PvP игр — {pvp_stats['total_pvp_games']}</blockquote>
    <blockquote>📈 Винрейт — {win_rate:.1f}%</blockquote>
    <blockquote>⏲ Аккаунту — {days} {pluralize(days, 'день', 'дня', 'дней')}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
        
        elif action == 'main':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            rank = get_user_rank(user['total_bets'])
            await callback.message.edit_text(
                f"🐝 <b>BeeCube</b>\n\n"
                f"👋 Привет, {callback.from_user.first_name}!\n\n"
                f"💰 Баланс — ${user['balance']:.0f}\n"
                f"<blockquote>🏆 Ваш ранг — {rank}</blockquote>",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
    
    @dp.callback_query(lambda c: c.data.startswith('top_'))
    async def top_callbacks(callback: CallbackQuery):
        action = callback.data.replace('top_', '')
        
        if action == 'refresh':
            await callback.answer()
            players, title = db.get_top_players_custom('total_win_amount', 10)
            text = f"🏆 <b>ТОП-10 ИГРОКОВ (обновлено)</b>\n{title}\n\n"
            if players:
                for i, player in enumerate(players, 1):
                    name = player['first_name'] or f"Игрок {player['user_id']}"
                    if player['username']:
                        name = f"@{player['username']}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
                    text += f"{medal} {i}. {name}\n"
                    text += f"<blockquote>💰 Выиграно: ${player['value']:.0f}</blockquote>\n\n"
            else:
                text += "Пока нет игроков в топе. Стань первым!"
            await callback.message.edit_text(text, reply_markup=get_top_keyboard())
        
        elif action == 'profile':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            reg_date = user['registered_date'] if isinstance(user['registered_date'], datetime) else datetime.strptime(user['registered_date'][:10], "%Y-%m-%d")
            days = (datetime.now() - reg_date).days
            rank = get_user_rank(user['total_bets'])
            rank_text, vip_progress = get_vip_progress(user['total_bets'])
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            pvp_stats = db.get_pvp_stats(user_id)
            text = f"""
    👤 <b>Ваш профиль ›</b>

    <blockquote>💰 Баланс — ${user['balance']:.0f}</blockquote>

    <blockquote>🏆 Ваш ранг — {rank}</blockquote>
    <blockquote>📊 VIP прогресс — {vip_progress:.0f}%</blockquote>
    <blockquote>{rank_text}</blockquote>

    <blockquote>🪙 Оборот — {format_number(user['total_bets'])}</blockquote>
    <blockquote>🎮 Сыграно — {user['total_games']} ставок</blockquote>
    <blockquote>⚔️ PvP игр — {pvp_stats['total_pvp_games']}</blockquote>
    <blockquote>📈 Винрейт — {win_rate:.1f}%</blockquote>
    <blockquote>⏲ Аккаунту — {days} {pluralize(days, 'день', 'дня', 'дней')}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
        
        elif action == 'stats':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
            text = f"""
    📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>

    <blockquote>💰 Баланс: ${user['balance']:.0f}</blockquote>
    <blockquote>🪙 Оборот: {format_number(user['total_bets'])}</blockquote>
    <blockquote>🏆 Выиграно: {format_number(user['total_win_amount'])}</blockquote>

    <blockquote>🎮 Сыграно игр: {user['total_games']}</blockquote>
    <blockquote>✅ Побед: {user['total_wins']}</blockquote>
    <blockquote>❌ Поражений: {user['total_games'] - user['total_wins']}</blockquote>

    <blockquote>📈 Макс. винстрик: {user['max_win_streak']}</blockquote>
    <blockquote>📊 Текущий винстрик: {user['current_win_streak']}</blockquote>
    <blockquote>💎 Ставок сегодня: {user['today_bets']:.0f}</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
        
        elif action == 'pvp':
            await callback.answer()
            user_id = callback.from_user.id
            pvp_stats = db.get_pvp_stats(user_id)
            win_rate = (pvp_stats['total_pvp_wins'] / pvp_stats['total_pvp_games'] * 100) if pvp_stats['total_pvp_games'] > 0 else 0
            text = f"""
    ⚔️ <b>PVP СТАТИСТИКА</b>

    <blockquote>🎮 Всего PvP игр: {pvp_stats['total_pvp_games']}</blockquote>
    <blockquote>✅ Побед: {pvp_stats['total_pvp_wins']}</blockquote>
    <blockquote>❌ Поражений: {pvp_stats['total_pvp_games'] - pvp_stats['total_pvp_wins']}</blockquote>
    <blockquote>💰 Выиграно: ${pvp_stats['total_pvp_win_amount']:.0f}</blockquote>
    <blockquote>📈 Винрейт: {win_rate:.1f}%</blockquote>"""
            await callback.message.edit_text(text, reply_markup=get_top_keyboard())
        
        elif action == 'main':
            await callback.answer()
            user_id = callback.from_user.id
            user = db.get_user(user_id)
            rank = get_user_rank(user['total_bets'])
            await callback.message.edit_text(
                f"🐝 <b>BeeCube</b>\n\n"
                f"👋 Привет, {callback.from_user.first_name}!\n\n"
                f"💰 Баланс — ${user['balance']:.0f}\n"
                f"<blockquote>🏆 Ваш ранг — {rank}</blockquote>",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
    
    @dp.message(PromoStates.waiting_for_code)
    async def process_promo_code(message: Message, state: FSMContext):
        code = message.text.upper().strip()
        user_id = message.from_user.id
        amount = db.use_promocode(code, user_id)
        
        if amount:
            new_balance = db.get_balance(user_id)
            await message.answer(
                f"✅ <b>Промокод активирован!</b>\n\n"
                f"<blockquote>🎟 Код: {code}</blockquote>\n"
                f"<blockquote>💰 Получено: +${amount:.2f}</blockquote>\n"
                f"<blockquote>💎 Новый баланс: ${new_balance:.0f}</blockquote>",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
        else:
            await message.answer(
                "❌ <b>Промокод недействителен</b>\n\n"
                "Возможные причины:\n"
                "• Код введен неверно\n"
                "• Промокод уже использован\n"
                "• Срок действия истек",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
        await state.clear()
    
    @dp.callback_query(lambda c: c.data.startswith('withdraw_confirm_'))
    async def withdraw_confirm(callback: CallbackQuery):
        await callback.answer()
        amount = float(callback.data.replace('withdraw_confirm_', ''))
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        
        if user['balance'] < amount:
            await callback.message.edit_text("❌ Недостаточно средств")
            return
        
        transfer = await crypto.transfer(user_id, amount * 0.1)
        
        if transfer and transfer.get('status') == 'completed':
            if await db.update_balance(user_id, -amount):
                saved = await db.save_transaction(user_id, 'withdraw', amount, 'completed', transfer_id=transfer.get('transfer_id'))
                if saved:
                    new_balance = db.get_balance(user_id)
                    await log_withdraw(user_id, amount, "completed")
                    await callback.message.edit_text(
                        f"✅ <b>ВЫВОД ВЫПОЛНЕН</b>\n\n"
                        f"<blockquote>💰 Сумма: ${amount:.2f}</blockquote>\n"
                        f"<blockquote>💎 Новый баланс: ${new_balance:.0f}</blockquote>"
                    )
                else:
                    await db.update_balance(user_id, amount)
                    await callback.message.edit_text("❌ Ошибка: транзакция уже была обработана")
            else:
                await callback.message.edit_text("❌ Ошибка при списании средств")
        else:
            await log_withdraw(user_id, amount, "failed")
            await callback.message.edit_text("❌ Ошибка вывода. Средства не списаны.")