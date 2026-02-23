# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram import F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from utils import is_admin, get_game_key_by_command, log_pvp_game
from config import GAME_RULES
import asyncio

pvp_games = {}
user_active_games = {}

async def pvp_menu(message: Message):
    # Эта функция вызывается при командах /cube, /foot и т.д.
    # Вся логика уже есть в обработчике cmd_pvp_game
    pass

def register_pvp_handlers(dp):
    @dp.message(Command("cube", "foot", "basket", "bowl", "darts", "slots"))
    async def cmd_pvp_game(message: Message):
        if message.chat.type == ChatType.PRIVATE:
            await message.answer("❌ PvP игры доступны только в групповых чатах!")
            return
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if db.is_banned(user_id):
            await message.answer("🚫 Вы забанены в боте.")
            return
        
        if user_id in user_active_games:
            await message.answer("❌ У вас уже есть активная игра в другом чате! Завершите её сначала.")
            return
        
        if not db.are_games_enabled() and not is_admin(user_id):
            await message.answer("⏸ Игры временно приостановлены")
            return
        
        command = message.text.split()[0]
        game_key = get_game_key_by_command(command)
        game_data = GAME_RULES[game_key]
        game_num = list(GAME_RULES.keys()).index(game_key)
        emoji = db.get_game_emoji(game_num)
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(f"❌ Укажите ставку!\nПример: {command} 10")
            return
        
        try:
            bet = float(args[1].replace(',', '.'))
            min_bet = db.get_min_bet()
            if bet < min_bet:
                await message.answer(f"❌ Минимальная ставка: ${min_bet}")
                return
        except ValueError:
            await message.answer("❌ Неверная сумма ставки")
            return
        
        balance = db.get_balance(user_id)
        if balance < bet:
            await message.answer(f"❌ Недостаточно средств!\nБаланс: ${balance:.2f}")
            return
        
        if chat_id in pvp_games:
            await message.answer("❌ В этом чате уже есть активная игра! Дождитесь её завершения.")
            return
        
        pvp_multiplier = db.get_pvp_multiplier()
        
        pvp_games[chat_id] = {"creator": user_id, "game_type": game_key, "bet": bet, "players": [user_id], "status": "waiting", "message_id": None}
        user_active_games[user_id] = chat_id
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ ВОЙТИ В ИГРУ", callback_data=f"pvp_join_{chat_id}")
        builder.button(text="❌ ОТМЕНА", callback_data=f"pvp_cancel_{chat_id}")
        
        sent = await message.answer(
            f"⚔️<b>PvP</b>\n"
            f"🎮<b>Режим:</b> {emoji} {game_data['name']}\n"
            f"1️⃣<b>Участник:</b> {message.from_user.first_name}\n"
            f"🪙<b>Ставка:</b> ${bet}\n"
            f"🕒<b>Статус:</b> ожидание второго игрока...\n"
            f"🕹️<b>Коэффициент:</b> {pvp_multiplier}\n\n"
            f"<blockquote>Нажмите кнопку чтобы войти в игру!</blockquote>",
            reply_markup=builder.as_markup()
        )
        pvp_games[chat_id]["message_id"] = sent.message_id
    
    @dp.callback_query(lambda c: c.data.startswith('pvp_join_'))
    async def pvp_join(callback: CallbackQuery):
        await callback.answer()
        chat_id = int(callback.data.replace('pvp_join_', ''))
        user_id = callback.from_user.id
        
        if chat_id not in pvp_games:
            await callback.message.edit_text("❌ Игра уже завершена!")
            return
        
        game = pvp_games[chat_id]
        
        if user_id == game["creator"]:
            await callback.answer("❌ Нельзя играть с самим собой!", show_alert=True)
            return
        
        if len(game["players"]) >= 2:
            await callback.answer("❌ Игра уже заполнена!", show_alert=True)
            return
        
        if db.is_banned(user_id):
            await callback.answer("🚫 Вы забанены в боте!", show_alert=True)
            return
        
        if user_id in user_active_games:
            await callback.answer("❌ У вас уже есть активная игра в другом чате!", show_alert=True)
            return
        
        balance = db.get_balance(user_id)
        if balance < game["bet"]:
            await callback.answer(f"❌ Недостаточно средств! Нужно: ${game['bet']}", show_alert=True)
            return
        
        game["players"].append(user_id)
        game["status"] = "playing"
        user_active_games[user_id] = chat_id
        
        await db.update_balance(game["creator"], -game["bet"])
        await db.update_balance(user_id, -game["bet"])
        
        creator_chat = await callback.bot.get_chat_member(chat_id, game["creator"])
        creator_name = creator_chat.user.first_name
        opponent_name = callback.from_user.first_name
        game_data = GAME_RULES[game["game_type"]]
        game_num = list(GAME_RULES.keys()).index(game["game_type"])
        emoji = db.get_game_emoji(game_num)
        
        await callback.message.edit_text(
            f"⚔️<b>PvP</b>\n"
            f"🎮<b>Режим:</b> {emoji} {game_data['name']}\n"
            f"1️⃣<b>Участник:</b> {creator_name}\n"
            f"2️⃣<b>Участник:</b> {opponent_name}\n"
            f"🪙<b>Ставка:</b> ${game['bet']}\n\n"
            f"<blockquote>⚡️ Бросаем кубики...</blockquote>"
        )
        
        await asyncio.sleep(2)
        msg1 = await callback.bot.send_dice(chat_id, emoji=emoji)
        await asyncio.sleep(3)
        msg2 = await callback.bot.send_dice(chat_id, emoji=emoji)
        await asyncio.sleep(3)
        
        result1, result2 = msg1.dice.value, msg2.dice.value
        
        if result1 == result2:
            await db.update_balance(game["creator"], game["bet"])
            await db.update_balance(user_id, game["bet"])
            await callback.message.answer(
                f"⚔️<b>PvP</b>\n"
                f"🎮<b>Режим:</b> {emoji} {game_data['name']}\n"
                f"1️⃣<b>Участник:</b> {creator_name} - {result1}\n"
                f"2️⃣<b>Участник:</b> {opponent_name} - {result2}\n\n"
                f"<blockquote>🤝 НИЧЬЯ! Ставки возвращены</blockquote>"
            )
            db.update_pvp_stats(game["creator"], False, 0)
            db.update_pvp_stats(user_id, False, 0)
            del pvp_games[chat_id]
            if game["creator"] in user_active_games:
                del user_active_games[game["creator"]]
            if user_id in user_active_games:
                del user_active_games[user_id]
            return
        
        winner_id = game["creator"] if result1 > result2 else user_id
        winner_name = creator_name if result1 > result2 else opponent_name
        loser_id = user_id if result1 > result2 else game["creator"]
        
        pvp_multiplier = db.get_pvp_multiplier()
        win_amount = game["bet"] * pvp_multiplier
        await db.update_balance(winner_id, win_amount)
        db.update_pvp_stats(winner_id, True, win_amount)
        db.update_pvp_stats(loser_id, False, 0)
        db.save_pvp_game(chat_id, game["creator"], user_id, game_data['name'], game["bet"], result1, result2, winner_id, win_amount)
        await log_pvp_game(chat_id, game["creator"], user_id, game_data['name'], game["bet"], winner_id, win_amount)
        
        await callback.message.answer(
            f"⚔️<b>PvP</b>\n"
            f"🎮<b>Режим:</b> {emoji} {game_data['name']}\n"
            f"1️⃣<b>Участник:</b> {creator_name} - {result1}\n"
            f"2️⃣<b>Участник:</b> {opponent_name} - {result2}\n\n"
            f"🥇<b>Победитель:</b> {winner_name}\n"
            f"<blockquote>💰 Выигрыш: +${win_amount:.2f} (x{pvp_multiplier})</blockquote>"
        )
        
        del pvp_games[chat_id]
        if game["creator"] in user_active_games:
            del user_active_games[game["creator"]]
        if user_id in user_active_games:
            del user_active_games[user_id]
    
    @dp.callback_query(lambda c: c.data.startswith('pvp_cancel_'))
    async def pvp_cancel(callback: CallbackQuery):
        await callback.answer()
        chat_id = int(callback.data.replace('pvp_cancel_', ''))
        user_id = callback.from_user.id
        
        if chat_id not in pvp_games:
            await callback.message.edit_text("❌ Игра уже завершена!")
            return
        
        game = pvp_games[chat_id]
        if user_id != game["creator"]:
            await callback.answer("❌ Только создатель может отменить игру!", show_alert=True)
            return
        
        await callback.message.edit_text("❌ Игра отменена создателем.")
        del pvp_games[chat_id]
        if game["creator"] in user_active_games:
            del user_active_games[game["creator"]]