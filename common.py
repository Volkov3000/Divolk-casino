# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram import F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from database import db
from utils import get_user_rank, is_admin, get_game_key_by_command, crypto
from keyboards import get_main_keyboard, get_games_keyboard, get_cancel_keyboard, get_repeat_keyboard
from config import GAME_RULES, THROW_DESCRIPTIONS, GameStates, logger
import asyncio

async def games_menu(message: Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        await message.answer("🚫 Вы забанены в боте.")
        return
    if not db.are_games_enabled() and not is_admin(user_id):
        await message.answer("⏸ Игры временно приостановлены")
        return
    user = db.get_user(user_id)
    min_bet = db.get_min_bet()
    await message.answer_photo(
        photo=types.FSInputFile("images/games.png"),
        caption=f"🎮 <b>Выбирайте игру или режим!</b>\n\n"
                f"💰 Баланс — ${user['balance']:.0f}\n"
                f"📉 Мин. ставка — ${min_bet}\n\n"
                f"После выбора игры введи сумму ставки:",
        reply_markup=get_games_keyboard()
    )

async def play_game(message: Message, bet: float, game_key: str):
    user_id = message.from_user.id
    game_data = GAME_RULES[game_key]
    user = db.get_user(user_id)
    
    min_bet = db.get_min_bet()
    if bet < min_bet:
        await message.answer(f"{game_data['emoji']} <b>Недостаточная ставка</b>\n\n<blockquote>💰 Минимум: ${min_bet}</blockquote>", reply_markup=get_games_keyboard())
        return False
    
    balance = db.get_balance(user_id)
    if balance < bet:
        await message.answer(f"{game_data['emoji']} <b>Недостаточно средств</b>\n\n<blockquote>💰 Баланс: ${balance:.2f}</blockquote>", reply_markup=get_games_keyboard())
        return False
    
    if not await db.update_balance(user_id, -bet):
        await message.answer("❌ Ошибка при списании средств")
        return False
    
    game_multiplier = db.get_game_multiplier(game_key)
    rank = get_user_rank(user['total_bets'])
    
    status_msg = await message.answer(
        f"{game_data['emoji']} <b>Вы ставите ${bet:.2f} на {game_data['name']}</b>\n\n"
        f"<blockquote>🏆 Ранг: {rank}</blockquote>\n"
        f"<blockquote>📊 Коэффициент: x{game_multiplier}</blockquote>\n"
        f"<blockquote>💰 Ожидаемый выигрыш: ${bet * game_multiplier:.2f}</blockquote>"
    )
    await asyncio.sleep(1.5)
    try:
        await status_msg.delete()
    except:
        pass
    
    game_num = list(GAME_RULES.keys()).index(game_key)
    emoji = db.get_game_emoji(game_num)
    msg = await message.answer_dice(emoji=emoji)
    await asyncio.sleep(2.5)
    
    value = msg.dice.value
    result_description = THROW_DESCRIPTIONS.get(game_data.get("description_key", emoji), {}).get(value, "Неизвестно")
    
    win = 0
    multiplier_used = 0
    
    if game_key == "dice":
        if value in game_data["win_values"]:
            multiplier_used = game_data["multiplier"][value]
            win = bet * multiplier_used
    else:
        if value in game_data["win_values"]:
            multiplier_used = game_multiplier
            win = bet * multiplier_used
    
    if win > 0:
        await db.update_balance(user_id, win)
        db.update_game_stats(user_id, bet, win, game_data['name'])
        db.save_game(user_id, game_data['name'], bet, value, win, multiplier_used)
        new_balance = db.get_balance(user_id)
        await message.answer(
            f"{emoji} <b>ПОБЕДА!</b>\n\n"
            f"<blockquote>🎮 Результат: {result_description}</blockquote>\n"
            f"<blockquote>💰 Выигрыш: +${win:.2f} (x{multiplier_used})</blockquote>\n"
            f"<blockquote>💎 Баланс: ${new_balance:.2f}</blockquote>",
            reply_markup=get_repeat_keyboard(game_key)
        )
    else:
        db.update_game_stats(user_id, bet, 0, game_data['name'])
        db.save_game(user_id, game_data['name'], bet, value, 0, 0)
        new_balance = db.get_balance(user_id)
        await message.answer(
            f"{emoji} <b>ПРОИГРЫШ</b>\n\n"
            f"<blockquote>🎮 Результат: {result_description}</blockquote>\n"
            f"<blockquote>💎 Баланс: ${new_balance:.2f}</blockquote>\n"
            f"Попробуй снова!",
            reply_markup=get_repeat_keyboard(game_key)
        )
    return True

def register_common_handlers(dp):
    from handlers.profile import register_profile_handlers
    from handlers.games import register_games_handlers
    from handlers.pvp import register_pvp_handlers
    from handlers.admin import register_admin_handlers
    
    register_profile_handlers(dp)
    register_games_handlers(dp)
    register_pvp_handlers(dp)
    register_admin_handlers(dp)
    
    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        referrer_id = None
        if message.text and len(message.text.split()) > 1:
            args = message.text.split()[1]
            if args.isdigit():
                referrer_id = int(args)
                if referrer_id == user_id:
                    referrer_id = None
        
        user = db.get_user(user_id)
        if not user:
            db.create_user(user_id, username, first_name, referrer_id)
            user = db.get_user(user_id)
            await message.answer("🎉 Добро пожаловать!")
        
        if db.is_banned(user_id):
            await message.answer("🚫 Вы забанены в боте.")
            return
        
        rank = get_user_rank(user['total_bets'])
        
        await message.answer_photo(
            photo=types.FSInputFile("images/profile.png"),
            caption=f"🐝 <b>BeeCube</b>\n\n"
                    f"👋 Привет, {first_name}!\n\n"
                    f"💰 Баланс — ${user['balance']:.0f}\n"
                    f"<blockquote>🏆 Ваш ранг — {rank}</blockquote>\n\n"
                    f"Каждый ход приближает к победе!",
            reply_markup=get_main_keyboard(is_admin(user_id))
        )
    
    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state:
            await state.clear()
            await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard(is_admin(message.from_user.id)))
        else:
            await message.answer("❌ Нет активного действия")
    
    @dp.message(F.text.in_(["🎮 ИГРАТЬ", "👤 ПРОФИЛЬ", "📥 ДЕПОЗИТ", "📤 ВЫВОД", "ℹ️ О ПРОЕКТЕ", "🏆 ТОП", "👑 АДМИН", "◀️ НАЗАД", "❌ ОТМЕНА"]))
    async def handle_menu_buttons(message: Message, state: FSMContext):
        text = message.text
        if text == "🎮 ИГРАТЬ":
            await games_menu(message)
        elif text == "👤 ПРОФИЛЬ":
            from handlers.profile import profile_menu
            await profile_menu(message)
        elif text == "📥 ДЕПОЗИТ":
            from handlers.profile import deposit_menu
            await deposit_menu(message, state)
        elif text == "📤 ВЫВОД":
            from handlers.profile import withdraw_menu
            await withdraw_menu(message)
        elif text == "ℹ️ О ПРОЕКТЕ":
            from handlers.profile import about_menu
            await about_menu(message)
        elif text == "🏆 ТОП":
            from handlers.profile import top_menu
            await top_menu(message)
        elif text == "👑 АДМИН":
            from handlers.admin import admin_menu
            await admin_menu(message)
        elif text == "◀️ НАЗАД":
            await cmd_start(message)
        elif text == "❌ ОТМЕНА":
            await state.clear()
            user_id = message.from_user.id
            await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard(is_admin(user_id)))
    
    @dp.message()
    async def handle_unknown_message(message: Message):
        user_id = message.from_user.id
        user = db.get_user(user_id)
        if not user:
            db.create_user(user_id, message.from_user.username, message.from_user.first_name)
            await message.answer("✅ Вы автоматически зарегистрированы! Используйте /start для начала.")
            logger.info(f"User auto-registered: {user_id}")