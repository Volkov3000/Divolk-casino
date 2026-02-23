# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from utils import is_valid_amount, is_admin, crypto
from keyboards import get_games_keyboard, get_repeat_keyboard
from config import GameStates, DISPLAY_TIMEOUT
import asyncio

# Функция play_game больше не импортируется, она будет доступна через common
# но мы не импортируем ее здесь, чтобы избежать цикла

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

def register_games_handlers(dp):
    # Импортируем play_game здесь, внутри функции, чтобы избежать циклического импорта
    from handlers.common import play_game
    
    @dp.message(lambda message: message.text and any(message.text.startswith(emoji) for emoji in ["🎰", "🎳", "⚽", "🏀", "🎯", "🎲"]))
    async def choose_game(message: Message, state: FSMContext):
        user_id = message.from_user.id
        if db.is_banned(user_id):
            await message.answer("🚫 Вы забанены в боте.")
            return
        
        emoji = message.text[0]
        game_key = db.get_game_by_emoji(emoji) or {"🎰": "slots", "🎳": "bowling", "⚽": "football", "🏀": "basketball", "🎯": "darts", "🎲": "dice"}.get(emoji, "dice")
        
        await state.update_data({"game_key": game_key})
        await state.set_state(GameStates.waiting_for_bet)
        
        user = db.get_user(user_id)
        min_bet = db.get_min_bet()
        await message.answer(
            f"<blockquote>💰 Твой баланс: ${user['balance']:.0f}</blockquote>\n\n"
            f"Введи сумму ставки (мин. ${min_bet}):",
            reply_markup=get_games_keyboard()
        )
    
    @dp.callback_query(lambda c: c.data.startswith('repeat_game_'))
    async def repeat_game(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        game_key = callback.data.replace('repeat_game_', '')
        user_id = callback.from_user.id
        
        if db.is_banned(user_id):
            await callback.message.answer("🚫 Вы забанены в боте.")
            return
        if not db.are_games_enabled() and not is_admin(user_id):
            await callback.message.answer("⏸ Игры временно приостановлены")
            return
        
        await state.update_data({"game_key": game_key})
        await state.set_state(GameStates.waiting_for_bet)
        
        user = db.get_user(user_id)
        min_bet = db.get_min_bet()
        await callback.message.answer(
            f"<blockquote>💰 Твой баланс: ${user['balance']:.0f}</blockquote>\n\n"
            f"Введи сумму ставки для повтора (мин. ${min_bet}):",
            reply_markup=get_games_keyboard()
        )
    
    @dp.message(lambda message: is_valid_amount(message.text))
    async def handle_number_input(message: Message, state: FSMContext):
        current_state = await state.get_state()
        text = message.text.replace(' ', '').replace(',', '.')
        user_id = message.from_user.id
        
        user = db.get_user(user_id)
        if not user:
            db.create_user(user_id, message.from_user.username, message.from_user.first_name)
        
        if not current_state:
            return
        
        if current_state == GameStates.waiting_for_bet.state:
            try:
                bet = float(text)
                min_bet = db.get_min_bet()
                if bet < min_bet:
                    await message.answer(f"❌ Минимальная ставка: ${min_bet}")
                    return
                data = await state.get_data()
                game_key = data.get('game_key', 'dice')
                asyncio.create_task(play_game(message, bet, game_key))
                await state.clear()
            except ValueError:
                await message.answer("❌ Введи корректное число")
        
        elif current_state == GameStates.waiting_for_deposit.state:
            try:
                amount = float(text)
                min_deposit = db.get_min_deposit()
                if amount < min_deposit:
                    await message.answer(f"❌ Минимальная сумма: ${min_deposit}")
                    return
                
                invoice = await crypto.create_invoice(amount, user_id)
                if invoice:
                    crypto.add_pending_invoice(invoice['invoice_id'], user_id, amount, invoice['pay_url'], message)
                    builder = InlineKeyboardBuilder()
                    builder.button(text="💳 ОПЛАТИТЬ", url=invoice['pay_url'])
                    await message.answer(
                        f"✅ <b>СЧЕТ СОЗДАН</b>\n\n"
                        f"<blockquote>💰 Сумма: ${amount}</blockquote>\n"
                        f"<blockquote>⏱ Срок: {DISPLAY_TIMEOUT} сек</blockquote>\n\n"
                        f"Нажми кнопку ниже для оплаты:",
                        reply_markup=builder.as_markup()
                    )
                    await state.clear()
                else:
                    await message.answer("❌ Ошибка создания счета. Попробуй позже.")
            except ValueError:
                await message.answer("❌ Введи корректное число")