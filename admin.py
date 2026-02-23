# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from utils import is_admin, format_number, log_admin_balance, crypto
from keyboards import (
    get_admin_keyboard, get_balance_admin_keyboard, get_ban_admin_keyboard,
    get_promo_admin_keyboard, get_games_admin_keyboard, get_settings_admin_keyboard,
    get_game_multipliers_keyboard, get_network_admin_keyboard, get_user_action_keyboard,
    get_user_balance_keyboard, get_game_emoji_keyboard, get_pagination_keyboard,
    get_stats_management_keyboard, get_user_stats_fields_keyboard, get_pvp_stats_fields_keyboard,
    get_top_fields_keyboard, get_top_pvp_fields_keyboard, get_top_actions_keyboard,
    get_top_pvp_actions_keyboard, get_reset_stats_keyboard, get_balance_amount_keyboard,
    get_promo_amount_keyboard, get_promo_uses_keyboard, get_main_keyboard
)
from config import AdminStates, GAME_RULES, WITHDRAW_FEE
from datetime import datetime
import re
import asyncio
import os
import psutil
import platform

def register_admin_handlers(dp):
    @dp.callback_query(lambda c: c.data == "admin_close")
    async def admin_close(callback: CallbackQuery):
        await callback.answer()
        await callback.message.delete()
    
    @dp.callback_query(lambda c: c.data == "admin_main")
    async def admin_main(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("👑 <b>АДМИН ПАНЕЛЬ</b>\n\nВыбери действие:", reply_markup=get_admin_keyboard())
    
    # ========== SERVER STATS ==========
    @dp.callback_query(lambda c: c.data == "admin_server_stats")
    async def admin_server_stats(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        
        # Сбор информации о сервере
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        # Идеальные значения
        cpu_ideal = "30-50%"
        mem_ideal = "60-70%"
        disk_ideal = "70-80%"
        uptime_ideal = "более 7 дней"
        users_ideal = "до 1000 активных"
        
        users_count = db.get_all_users_count()
        active_users = db.get_active_users_count(1)
        
        text = f"""
📊 <b>SERVER STATISTICS</b>

<b>🖥️ ПРОЦЕССОР</b>
└ Загрузка: {cpu_percent}% (идеал: {cpu_ideal})

<b>💾 ПАМЯТЬ</b>
└ Всего: {memory.total / (1024**3):.1f} GB
└ Использовано: {memory.used / (1024**3):.1f} GB
└ Свободно: {memory.available / (1024**3):.1f} GB
└ Загрузка: {memory.percent}% (идеал: {mem_ideal})

<b>💿 ДИСК</b>
└ Всего: {disk.total / (1024**3):.1f} GB
└ Использовано: {disk.used / (1024**3):.1f} GB
└ Свободно: {disk.free / (1024**3):.1f} GB
└ Загрузка: {disk.used / disk.total * 100:.1f}% (идеал: {disk_ideal})

<b>⏰ СИСТЕМА</b>
└ ОС: {platform.system()} {platform.release()}
└ Время работы: {uptime.days} д {uptime.seconds//3600} ч
└ Идеал: {uptime_ideal}

<b>👥 ПОЛЬЗОВАТЕЛИ</b>
└ Всего: {users_count}
└ Активных сегодня: {active_users}
└ Идеал: {users_ideal}

🔄 <i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>
        """
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 ОБНОВИТЬ", callback_data="admin_server_stats"))
        builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    # ========== УПРАВЛЕНИЕ СЕТЬЮ ==========
    @dp.callback_query(lambda c: c.data == "admin_network_menu")
    async def admin_network_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current_network = db.get_network()
        await callback.message.edit_text(f"🌐 <b>ВЫБОР СЕТИ</b>\n\nТекущая сеть: {current_network.upper()}\n\nВыбери сеть:", reply_markup=get_network_admin_keyboard(current_network))
    
    @dp.callback_query(lambda c: c.data == "admin_network_mainnet")
    async def admin_network_mainnet(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        db.set_network("mainnet")
        crypto.network = "mainnet"
        crypto.update_token()
        await callback.message.edit_text("✅ Сеть изменена на MAINNET\n\nТеперь используются основные кошельки.", reply_markup=get_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_network_testnet")
    async def admin_network_testnet(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        db.set_network("testnet")
        crypto.network = "testnet"
        crypto.update_token()
        await callback.message.edit_text("✅ Сеть изменена на TESTNET\n\nТеперь используются тестовые кошельки.", reply_markup=get_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_toggle_games")
    async def admin_toggle_games(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.are_games_enabled()
        db.toggle_games(not current)
        status = "ВЫКЛЮЧЕНЫ" if current else "ВКЛЮЧЕНЫ"
        await callback.message.edit_text(f"✅ Игры {status}")
    
    # ========== НАСТРОЙКИ ==========
    @dp.callback_query(lambda c: c.data == "admin_settings_menu")
    async def admin_settings_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("⚙️ <b>НАСТРОЙКИ</b>\n\nВыбери параметр для изменения:", reply_markup=get_settings_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_settings_min_bet")
    async def admin_settings_min_bet(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.get_min_bet()
        await callback.message.edit_text(f"💰 <b>ИЗМЕНЕНИЕ МИНИМАЛЬНОЙ СТАВКИ</b>\n\nТекущее значение: ${current}\n\nВведи новое значение:")
        await state.set_state(AdminStates.waiting_for_min_bet)
    
    @dp.message(AdminStates.waiting_for_min_bet)
    async def admin_set_min_bet(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                await message.answer("❌ Значение должно быть больше 0")
                return
            db.set_min_bet(value)
            await message.answer(f"✅ Минимальная ставка изменена на ${value}", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    @dp.callback_query(lambda c: c.data == "admin_settings_min_deposit")
    async def admin_settings_min_deposit(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.get_min_deposit()
        await callback.message.edit_text(f"📥 <b>ИЗМЕНЕНИЕ МИНИМАЛЬНОГО ДЕПОЗИТА</b>\n\nТекущее значение: ${current}\n\nВведи новое значение:")
        await state.set_state(AdminStates.waiting_for_min_deposit)
    
    @dp.message(AdminStates.waiting_for_min_deposit)
    async def admin_set_min_deposit(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                await message.answer("❌ Значение должно быть больше 0")
                return
            db.set_min_deposit(value)
            await message.answer(f"✅ Минимальный депозит изменен на ${value}", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    @dp.callback_query(lambda c: c.data == "admin_settings_min_withdraw")
    async def admin_settings_min_withdraw(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.get_min_withdraw()
        await callback.message.edit_text(f"📤 <b>ИЗМЕНЕНИЕ МИНИМАЛЬНОГО ВЫВОДА</b>\n\nТекущее значение: ${current}\n\nВведи новое значение:")
        await state.set_state(AdminStates.waiting_for_min_withdraw)
    
    @dp.message(AdminStates.waiting_for_min_withdraw)
    async def admin_set_min_withdraw(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                await message.answer("❌ Значение должно быть больше 0")
                return
            db.set_min_withdraw(value)
            await message.answer(f"✅ Минимальный вывод изменен на ${value}", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    # ========== ИЗМЕНЕНИЕ КОМИССИИ ==========
    @dp.callback_query(lambda c: c.data == "admin_settings_withdraw_fee")
    async def admin_settings_withdraw_fee(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.get_withdraw_fee()
        await callback.message.edit_text(f"💸 <b>ИЗМЕНЕНИЕ КОМИССИИ ВЫВОДА</b>\n\nТекущее значение: {current*100:.0f}%\n\nВведи новое значение в процентах (например 5, 10, 15):")
        await state.set_state(AdminStates.waiting_for_withdraw_fee)
    
    @dp.message(AdminStates.waiting_for_withdraw_fee)
    async def admin_set_withdraw_fee(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value < 0 or value > 100:
                await message.answer("❌ Значение должно быть от 0 до 100")
                return
            # Конвертируем проценты в десятичную дробь
            fee_decimal = value / 100
            db.set_withdraw_fee(fee_decimal)
            await message.answer(f"✅ Комиссия вывода изменена на {value}%", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    @dp.callback_query(lambda c: c.data == "admin_settings_pvp_multiplier")
    async def admin_settings_pvp_multiplier(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        current = db.get_pvp_multiplier()
        await callback.message.edit_text(f"⚔️ <b>ИЗМЕНЕНИЕ PVP МНОЖИТЕЛЯ</b>\n\nТекущее значение: x{current}\n\nВведи новое значение (например 1.5, 2.0):")
        await state.set_state(AdminStates.waiting_for_pvp_multiplier)
    
    @dp.message(AdminStates.waiting_for_pvp_multiplier)
    async def admin_set_pvp_multiplier(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 1:
                await message.answer("❌ Множитель должен быть больше 1")
                return
            db.set_pvp_multiplier(value)
            await message.answer(f"✅ PvP множитель изменен на x{value}", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    @dp.callback_query(lambda c: c.data == "admin_settings_game_multipliers")
    async def admin_settings_game_multipliers(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("🎲 <b>ИЗМЕНЕНИЕ КОЭФФИЦИЕНТОВ ИГР</b>\n\nВыбери игру для изменения коэффициента:", reply_markup=get_game_multipliers_keyboard())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_game_multiplier_'))
    async def admin_game_multiplier(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        game_key = callback.data.replace('admin_game_multiplier_', '')
        game_data = GAME_RULES[game_key]
        current = db.get_game_multiplier(game_key)
        await state.update_data({"game_key": game_key})
        
        if game_key == "dice":
            await callback.message.edit_text(f"🎲 <b>ИЗМЕНЕНИЕ КОЭФФИЦИЕНТА ДЛЯ КУБИКА</b>\n\nДля кубика используются фиксированные коэффициенты:\n• 4 -> x1.4\n• 5 -> x1.6\n• 6 -> x1.9\n\nИзменить их нельзя.")
            await state.clear()
            return
        
        await callback.message.edit_text(f"{game_data['emoji']} <b>ИЗМЕНЕНИЕ КОЭФФИЦИЕНТА ДЛЯ {game_data['name']}</b>\n\nТекущее значение: x{current}\n\nВведи новое значение (например 2.5, 3.0):")
        await state.set_state(AdminStates.waiting_for_game_multiplier)
    
    @dp.message(AdminStates.waiting_for_game_multiplier)
    async def admin_set_game_multiplier(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 1:
                await message.answer("❌ Коэффициент должен быть больше 1")
                return
            data = await state.get_data()
            game_key = data.get('game_key')
            game_data = GAME_RULES[game_key]
            db.set_game_multiplier(game_key, value)
            await message.answer(f"✅ Коэффициент для {game_data['name']} изменен на x{value}", reply_markup=get_main_keyboard(True))
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    # ========== АДМИН: УПРАВЛЕНИЕ БАЛАНСОМ ==========
    @dp.callback_query(lambda c: c.data == "admin_balance_menu")
    async def admin_balance_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("💰 <b>УПРАВЛЕНИЕ БАЛАНСОМ</b>\n\nВыбери действие:", reply_markup=get_balance_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_balance_add")
    async def admin_balance_add_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.update_data({"action": "add"})
        await state.set_state(AdminStates.waiting_for_user_id)
        await callback.message.edit_text("➕ <b>ДОБАВЛЕНИЕ БАЛАНСА</b>\n\nВведи ID пользователя:")
    
    @dp.callback_query(lambda c: c.data == "admin_balance_remove")
    async def admin_balance_remove_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.update_data({"action": "remove"})
        await state.set_state(AdminStates.waiting_for_user_id)
        await callback.message.edit_text("➖ <b>СПИСАНИЕ БАЛАНСА</b>\n\nВведи ID пользователя:")
    
    @dp.message(AdminStates.waiting_for_user_id)
    async def admin_balance_user_id(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            if not user:
                await message.answer("❌ Пользователь с таким ID не найден")
                return
            data = await state.get_data()
            action = data.get("action")
            await state.update_data({"target_user_id": user_id})
            action_text = "➕ ДОБАВИТЬ" if action == "add" else "➖ ЗАБРАТЬ"
            await message.answer(
                f"{action_text}\n\n"
                f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
                f"🆔 ID: {user_id}\n"
                f"💰 Текущий баланс: ${user['balance']:.2f}\n\n"
                f"Выбери сумму:",
                reply_markup=get_balance_amount_keyboard(action, user_id)
            )
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректный ID (только цифры)")
    
    @dp.callback_query(lambda c: c.data.startswith('admin_balance_add_') or c.data.startswith('admin_balance_remove_'))
    async def admin_balance_amount_callback(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        
        # Парсим callback_data: admin_balance_add_123_10 или admin_balance_remove_123_10
        parts = callback.data.split('_')
        if len(parts) != 5:
            await callback.message.edit_text("❌ Ошибка формата данных")
            return
        
        action = parts[2]
        try:
            user_id = int(parts[3])
            amount = float(parts[4])
        except (ValueError, IndexError):
            await callback.message.edit_text("❌ Ошибка в данных")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        admin_id = callback.from_user.id
        
        if action == "add":
            if await db.update_balance(user_id, amount, admin_id):
                await db.save_transaction(user_id, 'admin_add', amount, 'completed', admin_id=admin_id)
                new_balance = db.get_balance(user_id)
                await log_admin_balance(user_id, amount, admin_id, "add")
                try:
                    await callback.bot.send_message(user_id, f"➕ <b>Вам начислено ${amount:.2f}</b>\n\nНовый баланс: ${new_balance:.2f}")
                except:
                    pass
                await callback.message.edit_text(
                    f"✅ Баланс пользователя {user['first_name']} пополнен на ${amount:.2f}\n"
                    f"💰 Новый баланс: ${new_balance:.2f}",
                    reply_markup=get_admin_keyboard()
                )
            else:
                await callback.message.edit_text("❌ Ошибка при пополнении баланса")
        
        elif action == "remove":
            if user['balance'] < amount:
                await callback.message.edit_text(f"❌ У пользователя недостаточно средств. Баланс: ${user['balance']:.2f}")
                return
            if await db.update_balance(user_id, -amount, admin_id):
                await db.save_transaction(user_id, 'admin_remove', amount, 'completed', admin_id=admin_id)
                new_balance = db.get_balance(user_id)
                await log_admin_balance(user_id, -amount, admin_id, "remove")
                try:
                    await callback.bot.send_message(user_id, f"➖ <b>У вас списано ${amount:.2f}</b>\n\nНовый баланс: ${new_balance:.2f}")
                except:
                    pass
                await callback.message.edit_text(
                    f"✅ У пользователя {user['first_name']} списано ${amount:.2f}\n"
                    f"💰 Новый баланс: ${new_balance:.2f}",
                    reply_markup=get_admin_keyboard()
                )
            else:
                await callback.message.edit_text("❌ Ошибка при списании баланса")
    
    # ========== АДМИН: УПРАВЛЕНИЕ ПРОМОКОДАМИ ==========
    @dp.callback_query(lambda c: c.data == "admin_promo_menu")
    async def admin_promo_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("🎟 <b>УПРАВЛЕНИЕ ПРОМОКОДАМИ</b>\n\nВыбери действие:", reply_markup=get_promo_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_promo_create")
    async def admin_promo_create_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_promo_code)
        await callback.message.edit_text("🎟 <b>СОЗДАНИЕ ПРОМОКОДА</b>\n\nВведи код промокода (только буквы и цифры):")
    
    @dp.message(AdminStates.waiting_for_promo_code)
    async def admin_promo_code(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        code = message.text.upper().strip()
        if not re.match(r'^[A-Z0-9]+$', code):
            await message.answer("❌ Код должен содержать только буквы и цифры")
            return
        await state.update_data({"promo_code": code})
        await message.answer(f"🎟 Код: {code}\n\nВыбери сумму начисления:", reply_markup=get_promo_amount_keyboard())
        # Не очищаем state, продолжаем в callback
    
    @dp.callback_query(lambda c: c.data.startswith('admin_promo_amount_'))
    async def admin_promo_amount_callback(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        amount = float(callback.data.replace('admin_promo_amount_', ''))
        await state.update_data({"promo_amount": amount})
        await callback.message.edit_text(f"💰 Сумма: ${amount:.2f}\n\nВыбери количество использований:", reply_markup=get_promo_uses_keyboard())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_promo_uses_'))
    async def admin_promo_uses_callback(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        max_uses = int(callback.data.replace('admin_promo_uses_', ''))
        data = await state.get_data()
        code = data.get("promo_code")
        amount = data.get("promo_amount")
        admin_id = callback.from_user.id
        
        if not code or not amount:
            await callback.message.edit_text("❌ Ошибка: не все данные заполнены")
            await state.clear()
            return
        
        promocode_id = db.create_promocode(code, amount, max_uses, admin_id)
        if promocode_id:
            await callback.message.edit_text(
                f"✅ <b>Промокод создан!</b>\n\n"
                f"🎟 Код: {code}\n"
                f"💰 Сумма: ${amount:.2f}\n"
                f"📊 Использований: {max_uses}\n"
                f"👤 Создал: {callback.from_user.first_name}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await callback.message.edit_text("❌ Промокод с таким кодом уже существует")
        await state.clear()
    
    @dp.callback_query(lambda c: c.data == "admin_promo_list")
    async def admin_promo_list(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        promocodes = db.get_all_promocodes()
        if not promocodes:
            await callback.message.edit_text("📋 <b>СПИСОК ПРОМОКОДОВ</b>\n\nПока нет созданных промокодов.", reply_markup=get_promo_admin_keyboard())
            return
        text = "📋 <b>СПИСОК ПРОМОКОДОВ</b>\n\n"
        for promo in promocodes:
            status = "✅ Активен" if promo['is_active'] else "❌ Неактивен"
            expires = datetime.strptime(promo['expires_at'][:10], "%Y-%m-%d").strftime("%d.%m.%Y")
            text += f"<b>Код:</b> {promo['code']}\n"
            text += f"<blockquote>💰 Сумма: ${promo['amount']:.2f}</blockquote>\n"
            text += f"<blockquote>📊 Использовано: {promo['used_count']}/{promo['max_uses']}</blockquote>\n"
            text += f"<blockquote>📅 Действует до: {expires}</blockquote>\n"
            text += f"<blockquote>{status}</blockquote>\n\n"
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ НАЗАД", callback_data="admin_promo_menu")
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    # ========== АДМИН: ПОИСК ПОЛЬЗОВАТЕЛЕЙ ==========
    @dp.callback_query(lambda c: c.data == "admin_user_search")
    async def admin_user_search(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_search_query)
        await callback.message.edit_text("👥 <b>ПОИСК ПОЛЬЗОВАТЕЛЕЙ</b>\n\nВведи ID, username или имя для поиска (или 'все' для списка всех):")
    
    @dp.message(AdminStates.waiting_for_search_query)
    async def admin_search_results(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        query = message.text.strip()
        page = 1
        
        try:
            if query.lower() == 'все':
                users, total = db.get_all_users_paginated(page, 10)
            else:
                users, total = db.search_users_paginated(query, page, 10)
        except Exception as e:
            await message.answer(f"❌ Ошибка при поиске: {e}")
            await state.clear()
            return
        
        if not users:
            await message.answer("❌ Пользователи не найдены")
            await state.clear()
            return
        
        total_pages = (total + 9) // 10
        text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА: {query}</b>\n\nНайдено: {total}\nСтраница {page}/{total_pages}\n\n"
        keyboard = InlineKeyboardBuilder()
        
        for user in users:
            status = "🚫" if user['is_banned'] else "✅"
            text += f"{status} <b>{user['first_name']}</b> (@{user['username'] or 'нет'})\n"
            text += f"<blockquote>🆔 {user['user_id']} | 💰 ${user['balance']:.2f}</blockquote>\n\n"
            keyboard.button(text=f"👤 {user['first_name']} ({user['user_id']})", callback_data=f"admin_user_view_{user['user_id']}")
        
        keyboard.adjust(1)
        
        if total_pages > 1:
            pagination = get_pagination_keyboard(f"admin_search_{query}", page, total_pages)
            for btn in pagination.inline_keyboard:
                keyboard.row(*btn)
        
        keyboard.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
        
        await message.answer(text, reply_markup=keyboard.as_markup())
        await state.clear()
    
    @dp.callback_query(lambda c: c.data.startswith('admin_search_'))
    async def admin_search_pagination(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        
        # Формат: admin_search_query_page_2
        parts = callback.data.replace('admin_search_', '').split('_page_')
        if len(parts) != 2:
            await callback.message.edit_text("❌ Ошибка пагинации")
            return
        
        query = parts[0]
        try:
            page = int(parts[1])
        except ValueError:
            await callback.message.edit_text("❌ Ошибка номера страницы")
            return
        
        try:
            users, total = db.search_users_paginated(query, page, 10)
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при поиске: {e}")
            return
        
        total_pages = (total + 9) // 10
        text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА: {query}</b>\n\nНайдено: {total}\nСтраница {page}/{total_pages}\n\n"
        keyboard = InlineKeyboardBuilder()
        
        for user in users:
            status = "🚫" if user['is_banned'] else "✅"
            text += f"{status} <b>{user['first_name']}</b> (@{user['username'] or 'нет'})\n"
            text += f"<blockquote>🆔 {user['user_id']} | 💰 ${user['balance']:.2f}</blockquote>\n\n"
            keyboard.button(text=f"👤 {user['first_name']} ({user['user_id']})", callback_data=f"admin_user_view_{user['user_id']}")
        
        keyboard.adjust(1)
        
        if total_pages > 1:
            pagination = get_pagination_keyboard(f"admin_search_{query}", page, total_pages)
            for btn in pagination.inline_keyboard:
                keyboard.row(*btn)
        
        keyboard.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_main"))
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_user_view_'))
    async def admin_view_user(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_user_view_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        if isinstance(user['registered_date'], str):
            try:
                reg_date = datetime.strptime(user['registered_date'][:10], "%Y-%m-%d")
            except:
                reg_date = datetime.now()
        else:
            reg_date = user['registered_date']
        
        days = (datetime.now() - reg_date).days
        status = "ЗАБАНЕН" if user['is_banned'] else "АКТИВЕН"
        pvp_stats = db.get_pvp_stats(user_id)
        
        text = f"""
👤 <b>ПОЛЬЗОВАТЕЛЬ {user_id}</b>

📱 <b>Информация:</b>
<blockquote>🆔 ID: {user['user_id']}</blockquote>
<blockquote>👤 Имя: {user['first_name']}</blockquote>
<blockquote>📱 Username: @{user['username'] or 'нет'}</blockquote>
<blockquote>🚫 Статус: {status}</blockquote>
<blockquote>📅 С нами: {days} дн.</blockquote>

💰 <b>Финансы:</b>
<blockquote>Баланс: ${user['balance']:.2f}</blockquote>
<blockquote>Оборот: ${user['total_bets']:.2f}</blockquote>
<blockquote>Выиграно: ${user['total_win_amount']:.2f}</blockquote>

🎮 <b>Игры:</b>
<blockquote>Обычных игр: {user['total_games']} (побед: {user['total_wins']})</blockquote>
<blockquote>PvP игр: {pvp_stats['total_pvp_games']} (побед: {pvp_stats['total_pvp_wins']})</blockquote>
<blockquote>Выиграно в PvP: ${pvp_stats['total_pvp_win_amount']:.2f}</blockquote>

📊 <b>Дополнительно:</b>
<blockquote>Макс. винстрик: {user['max_win_streak']}</blockquote>
<blockquote>За сегодня: ${user['today_bets']:.2f}</blockquote>
<blockquote>Избранное: {user['favorite_game'] or 'нет'}</blockquote>"""
        
        await callback.message.edit_text(text, reply_markup=get_user_action_keyboard(user_id))
    
    @dp.callback_query(lambda c: c.data.startswith('admin_user_balance_'))
    async def admin_user_balance(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_user_balance_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        await state.update_data({"target_user_id": user_id})
        await callback.message.edit_text(
            f"💰 <b>УПРАВЛЕНИЕ БАЛАНСОМ</b>\n\n"
            f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Текущий баланс: ${user['balance']:.2f}\n\n"
            f"Выбери действие:",
            reply_markup=get_user_balance_keyboard(user_id)
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_balance_add_'))
    async def admin_balance_add_user(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_balance_add_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        await state.update_data({"target_user_id": user_id, "action": "add"})
        await callback.message.edit_text(
            f"➕ <b>ДОБАВЛЕНИЕ БАЛАНСА</b>\n\n"
            f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"🆔 ID: {user_id}\n
            f"💰 Текущий баланс: ${user['balance']:.2f}\n\n"
            f"Выбери сумму для добавления:",
            reply_markup=get_balance_amount_keyboard("add", user_id)
        )
        await state.clear()
    
    @dp.callback_query(lambda c: c.data.startswith('admin_balance_remove_'))
    async def admin_balance_remove_user(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_balance_remove_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        await state.update_data({"target_user_id": user_id, "action": "remove"})
        await callback.message.edit_text(
            f"➖ <b>СПИСАНИЕ БАЛАНСА</b>\n\n"
            f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Текущий баланс: ${user['balance']:.2f}\n\n"
            f"Выбери сумму для списания:",
            reply_markup=get_balance_amount_keyboard("remove", user_id)
        )
        await state.clear()
    
    # ========== АДМИН: УПРАВЛЕНИЕ БАНАМИ ==========
    @dp.callback_query(lambda c: c.data == "admin_ban_menu")
    async def admin_ban_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("🚫 <b>УПРАВЛЕНИЕ БАНАМИ</b>\n\nВыбери действие:", reply_markup=get_ban_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_ban_ban")
    async def admin_ban_ban_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_user_id)
        await callback.message.edit_text("🚫 <b>ЗАБАНИТЬ ПОЛЬЗОВАТЕЛЯ</b>\n\nВведи ID пользователя:")
    
    @dp.message(AdminStates.waiting_for_user_id)
    async def admin_ban_user_id(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            if not user:
                await message.answer("❌ Пользователь с таким ID не найден")
                await state.clear()
                return
            
            if user['is_banned']:
                await message.answer("❌ Пользователь уже забанен")
                await state.clear()
                return
            
            await state.update_data({"target_user_id": user_id})
            await state.set_state(AdminStates.waiting_for_ban_reason)
            
            await message.answer(
                f"🚫 <b>ЗАБАНИТЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
                f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
                f"🆔 ID: {user_id}\n\n"
                f"Введи причину бана:"
            )
        except ValueError:
            await message.answer("❌ Введи корректный ID (только цифры)")
            await state.clear()
    
    @dp.message(AdminStates.waiting_for_ban_reason)
    async def admin_ban_reason(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        reason = message.text.strip()
        data = await state.get_data()
        user_id = data.get("target_user_id")
        admin_id = message.from_user.id
        
        db.ban_user(user_id, reason, admin_id)
        
        await message.answer(
            f"✅ Пользователь {user_id} забанен\n\n"
            f"Причина: {reason}",
            reply_markup=get_main_keyboard(True)
        )
        await state.clear()
    
    @dp.callback_query(lambda c: c.data == "admin_ban_unban")
    async def admin_ban_unban_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_user_id)
        await callback.message.edit_text("✅ <b>РАЗБАНИТЬ ПОЛЬЗОВАТЕЛЯ</b>\n\nВведи ID пользователя:")
    
    @dp.message(AdminStates.waiting_for_user_id)
    async def admin_unban_user_id(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            if not user:
                await message.answer("❌ Пользователь с таким ID не найден")
                await state.clear()
                return
            
            if not user['is_banned']:
                await message.answer("❌ Пользователь не забанен")
                await state.clear()
                return
            
            db.unban_user(user_id)
            
            await message.answer(
                f"✅ Пользователь {user_id} разбанен",
                reply_markup=get_main_keyboard(True)
            )
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректный ID (только цифры)")
            await state.clear()
    
    @dp.callback_query(lambda c: c.data == "admin_ban_list")
    async def admin_ban_list(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        banned = db.get_banned_users()
        
        if not banned:
            await callback.message.edit_text("📋 <b>СПИСОК ЗАБАНЕННЫХ</b>\n\nНет забаненных пользователей.", reply_markup=get_ban_admin_keyboard())
            return
        
        text = "📋 <b>СПИСОК ЗАБАНЕННЫХ</b>\n\n"
        for ban in banned:
            user = db.get_user(ban['user_id'])
            name = user['first_name'] if user else f"ID {ban['user_id']}"
            username = f"@{user['username']}" if user and user['username'] else "нет username"
            ban_date = datetime.strptime(ban['banned_at'][:10], "%Y-%m-%d").strftime("%d.%m.%Y")
            
            text += f"<b>{name}</b> ({username})\n"
            text += f"<blockquote>🆔 {ban['user_id']}</blockquote>\n"
            text += f"<blockquote>📅 Дата: {ban_date}</blockquote>\n"
            text += f"<blockquote>📝 Причина: {ban['reason']}</blockquote>\n\n"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ НАЗАД", callback_data="admin_ban_menu")
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    # ========== АДМИН: УПРАВЛЕНИЕ ИГРАМИ (ЭМОДЗИ) ==========
    @dp.callback_query(lambda c: c.data == "admin_games_menu")
    async def admin_games_menu(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("🎮 <b>УПРАВЛЕНИЕ ИГРАМИ</b>\n\nВыбери игру для изменения эмодзи:", reply_markup=get_games_admin_keyboard())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_game_') and c.data != "admin_games_menu")
    async def admin_game_emoji(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            game_num = int(callback.data.replace('admin_game_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный номер игры")
            return
        
        current_emoji = db.get_game_emoji(game_num)
        game_name = list(GAME_RULES.values())[game_num]["name"]
        
        await callback.message.edit_text(
            f"{current_emoji} <b>ИЗМЕНЕНИЕ ЭМОДЗИ ДЛЯ {game_name}</b>\n\n"
            f"Текущий эмодзи: {current_emoji}\n\n"
            f"Выбери новый эмодзи:",
            reply_markup=get_game_emoji_keyboard(game_num, current_emoji)
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_game_emoji_'))
    async def admin_set_game_emoji(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        parts = callback.data.replace('admin_game_emoji_', '').split('_')
        if len(parts) != 2:
            await callback.message.edit_text("❌ Ошибка формата данных")
            return
        
        try:
            game_num = int(parts[0])
            emoji = parts[1]
        except ValueError:
            await callback.message.edit_text("❌ Ошибка в данных")
            return
        
        db.set_game_emoji(game_num, emoji)
        
        await callback.message.edit_text(
            f"✅ Эмодзи для игры изменено на {emoji}",
            reply_markup=get_admin_keyboard()
        )
    
    # ========== АДМИН: УПРАВЛЕНИЕ СТАТИСТИКОЙ ==========
    @dp.callback_query(lambda c: c.data == "admin_stats_management")
    async def admin_stats_management(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("📊 <b>УПРАВЛЕНИЕ СТАТИСТИКОЙ</b>\n\nВыбери что хочешь изменить:", reply_markup=get_stats_management_keyboard())
    
    @dp.callback_query(lambda c: c.data == "admin_stats_user")
    async def admin_stats_user(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_stats_user_id)
        await callback.message.edit_text("👤 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ</b>\n\nВведи ID пользователя:")
    
    @dp.message(AdminStates.waiting_for_stats_user_id)
    async def admin_stats_user_id(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            if not user:
                await message.answer("❌ Пользователь с таким ID не найден")
                await state.clear()
                return
            stats = db.get_user_stats_full(user_id)
            pvp_stats = db.get_pvp_stats(user_id)
            text = f"""
👤 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ {user_id}</b>

📱 <b>Информация:</b>
<blockquote>👤 Имя: {user['first_name']}</blockquote>
<blockquote>📱 Username: @{user['username'] or 'нет'}</blockquote>
<blockquote>🚫 Статус: {'ЗАБАНЕН' if user['is_banned'] else 'АКТИВЕН'}</blockquote>

💰 <b>Финансы:</b>
<blockquote>Баланс: ${user['balance']:.2f}</blockquote>
<blockquote>Оборот: ${user['total_bets']:.2f}</blockquote>
<blockquote>Выиграно: ${user['total_win_amount']:.2f}</blockquote>

🎮 <b>Обычные игры:</b>
<blockquote>Всего игр: {user['total_games']}</blockquote>
<blockquote>Побед: {user['total_wins']}</blockquote>
<blockquote>Поражений: {user['total_games'] - user['total_wins']}</blockquote>
<blockquote>Винрейт: {(user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0:.1f}%</blockquote>

⚔️ <b>PvP игры:</b>
<blockquote>Всего игр: {pvp_stats['total_pvp_games']}</blockquote>
<blockquote>Побед: {pvp_stats['total_pvp_wins']}</blockquote>
<blockquote>Выиграно: ${pvp_stats['total_pvp_win_amount']:.2f}</blockquote>

📊 <b>Дополнительно:</b>
<blockquote>Макс. винстрик: {user['max_win_streak']}</blockquote>
<blockquote>Тек. винстрик: {user['current_win_streak']}</blockquote>
<blockquote>Ставок сегодня: ${user['today_bets']:.2f}</blockquote>"""
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="✏️ Изменить обычную", callback_data=f"admin_stats_user_edit_{user_id}"),
                        InlineKeyboardButton(text="⚔️ Изменить PvP", callback_data=f"admin_stats_pvp_edit_{user_id}"))
            builder.row(InlineKeyboardButton(text="🔄 Сбросить", callback_data=f"admin_stats_user_reset_{user_id}"),
                        InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management"))
            await message.answer(text, reply_markup=builder.as_markup())
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректный ID (только цифры)")
            await state.clear()
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_user_edit_'))
    async def admin_stats_user_edit(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_stats_user_edit_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        await state.update_data({"stats_user_id": user_id})
        await callback.message.edit_text(
            f"👤 <b>ИЗМЕНЕНИЕ СТАТИСТИКИ</b>\n\n"
            f"Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"ID: {user_id}\n\n"
            f"Выбери поле для изменения:",
            reply_markup=get_user_stats_fields_keyboard(user_id)
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_user_field_'))
    async def admin_stats_user_field(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        parts = callback.data.replace('admin_stats_user_field_', '').split('_')
        if len(parts) < 2:
            await callback.message.edit_text("❌ Ошибка формата данных")
            return
        
        try:
            user_id = int(parts[0])
            field = parts[1]
        except ValueError:
            await callback.message.edit_text("❌ Ошибка в данных")
            return
        
        field_names = {'balance': '💰 Баланс', 'total_bets': '💸 Оборот', 'total_games': '🎮 Всего игр',
                       'total_wins': '✅ Побед', 'total_win_amount': '🏆 Выиграно', 'max_win_streak': '📈 Макс. винстрик',
                       'current_win_streak': '📊 Тек. винстрик', 'today_bets': '💎 Ставок сегодня'}
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        current_value = user.get(field, 0)
        await state.update_data({"stats_user_id": user_id, "stats_field": field})
        await state.set_state(AdminStates.waiting_for_stats_value)
        await callback.message.edit_text(
            f"✏️ <b>ИЗМЕНЕНИЕ {field_names.get(field, field)}</b>\n\n"
            f"👤 Пользователь: {user['first_name']}\n"
            f"🆔 ID: {user_id}\n"
            f"📊 Текущее значение: {current_value}\n\n"
            f"Введи новое значение:"
        )
    
    @dp.message(AdminStates.waiting_for_stats_value)
    async def admin_stats_set_value(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value < 0:
                await message.answer("❌ Значение не может быть отрицательным")
                return
            data = await state.get_data()
            user_id = data.get("stats_user_id")
            field = data.get("stats_field")
            stats_type = data.get("stats_type", "user")
            
            user = db.get_user(user_id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                await state.clear()
                return
            
            success = False
            if stats_type == "pvp":
                success = db.update_pvp_stat(user_id, field, value)
            else:
                success = db.update_user_stat(user_id, field, value)
            
            if success:
                if stats_type == "pvp":
                    new_stats = db.get_pvp_stats(user_id)
                    new_value = new_stats.get(field, 0)
                else:
                    new_user = db.get_user(user_id)
                    new_value = new_user.get(field, 0)
                
                await message.answer(
                    f"✅ <b>Статистика обновлена!</b>\n\n"
                    f"👤 Пользователь: {user['first_name']}\n"
                    f"📊 Поле: {field}\n"
                    f"🔄 Было: {user.get(field, 0)}\n"
                    f"➡️ Стало: {new_value}",
                    reply_markup=get_main_keyboard(True)
                )
            else:
                await message.answer("❌ Ошибка при обновлении статистики")
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_pvp_edit_'))
    async def admin_stats_pvp_edit(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_stats_pvp_edit_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        await state.update_data({"stats_user_id": user_id})
        await callback.message.edit_text(
            f"⚔️ <b>ИЗМЕНЕНИЕ PVP СТАТИСТИКИ</b>\n\n"
            f"Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"ID: {user_id}\n\n"
            f"Выбери поле для изменения:",
            reply_markup=get_pvp_stats_fields_keyboard(user_id)
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_pvp_field_'))
    async def admin_stats_pvp_field(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        parts = callback.data.replace('admin_stats_pvp_field_', '').split('_')
        if len(parts) < 2:
            await callback.message.edit_text("❌ Ошибка формата данных")
            return
        
        try:
            user_id = int(parts[0])
            field = parts[1]
        except ValueError:
            await callback.message.edit_text("❌ Ошибка в данных")
            return
        
        field_names = {'total_pvp_games': '🎮 Всего PvP игр', 'total_pvp_wins': '✅ Побед в PvP', 'total_pvp_win_amount': '💰 Выиграно в PvP'}
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        pvp_stats = db.get_pvp_stats(user_id)
        current_value = pvp_stats.get(field, 0)
        await state.update_data({"stats_user_id": user_id, "stats_field": field, "stats_type": "pvp"})
        await state.set_state(AdminStates.waiting_for_stats_value)
        await callback.message.edit_text(
            f"✏️ <b>ИЗМЕНЕНИЕ {field_names.get(field, field)}</b>\n\n"
            f"👤 Пользователь: {user['first_name']}\n"
            f"🆔 ID: {user_id}\n"
            f"📊 Текущее значение: {current_value}\n\n"
            f"Введи новое значение:"
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_user_reset_'))
    async def admin_stats_user_reset(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_stats_user_reset_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="✅ ДА, СБРОСИТЬ", callback_data=f"admin_stats_user_reset_confirm_{user_id}"),
                    InlineKeyboardButton(text="❌ ОТМЕНА", callback_data=f"admin_stats_user_edit_{user_id}"))
        
        await callback.message.edit_text(
            f"⚠️ <b>СБРОС СТАТИСТИКИ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            f"👤 Пользователь: {user['first_name']} (@{user['username'] or 'нет'})\n"
            f"🆔 ID: {user_id}\n\n"
            f"Ты уверен? Это действие нельзя отменить!",
            reply_markup=builder.as_markup()
        )
    
    @dp.callback_query(lambda c: c.data.startswith('admin_stats_user_reset_confirm_'))
    async def admin_stats_user_reset_confirm(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        try:
            user_id = int(callback.data.replace('admin_stats_user_reset_confirm_', ''))
        except ValueError:
            await callback.message.edit_text("❌ Неверный ID пользователя")
            return
        
        user = db.get_user(user_id)
        if db.reset_user_stats(user_id):
            await callback.message.edit_text(f"✅ <b>Статистика пользователя сброшена!</b>\n\n👤 Пользователь: {user['first_name']}\n🆔 ID: {user_id}", reply_markup=get_main_keyboard(True))
        else:
            await callback.message.edit_text("❌ Ошибка при сбросе статистики")
    
    # ========== АДМИН: УПРАВЛЕНИЕ ТОПОМ ==========
    @dp.callback_query(lambda c: c.data == "admin_stats_top")
    async def admin_stats_top(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("📊 <b>ТОП ИГРОКОВ</b>\n\nВыбери по какому полю показать топ:", reply_markup=get_top_fields_keyboard())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_top_view_'))
    async def admin_top_view(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        field = callback.data.replace('admin_top_view_', '')
        players, title = db.get_top_players_custom(field, 10)
        text = f"📊 <b>ТОП-10 ИГРОКОВ</b>\n{title}\n\n"
        if players:
            for i, player in enumerate(players, 1):
                name = player['first_name'] or f"Игрок {player['user_id']}"
                if player['username']:
                    name = f"@{player['username']}"
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                text += f"{medal} {name}\n"
                text += f"<blockquote>Значение: {player['value']:.2f}</blockquote>\n"
                text += f"<blockquote>🆔 {player['user_id']}</blockquote>\n\n"
        else:
            text += "Пока нет данных для топа."
        await callback.message.edit_text(text, reply_markup=get_top_actions_keyboard(field))
    
    @dp.callback_query(lambda c: c.data.startswith('admin_top_refresh_'))
    async def admin_top_refresh(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        field = callback.data.replace('admin_top_refresh_', '')
        players, title = db.get_top_players_custom(field, 10)
        text = f"📊 <b>ТОП-10 ИГРОКОВ (обновлено)</b>\n{title}\n\n"
        if players:
            for i, player in enumerate(players, 1):
                name = player['first_name'] or f"Игрок {player['user_id']}"
                if player['username']:
                    name = f"@{player['username']}"
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                text += f"{medal} {name}\n"
                text += f"<blockquote>Значение: {player['value']:.2f}</blockquote>\n"
                text += f"<blockquote>🆔 {player['user_id']}</blockquote>\n\n"
        else:
            text += "Пока нет данных для топа."
        await callback.message.edit_text(text, reply_markup=get_top_actions_keyboard(field))
    
    @dp.callback_query(lambda c: c.data.startswith('admin_top_edit_'))
    async def admin_top_edit(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        field = callback.data.replace('admin_top_edit_', '')
        players, title = db.get_top_players_custom(field, 10)
        if not players:
            await callback.message.edit_text("❌ В топе пока нет игроков")
            return
        text = f"✏️ <b>РЕДАКТИРОВАНИЕ ТОПА</b>\n{title}\n\nВведи номер позиции, которую хочешь изменить (1-10):\n\n"
        for i, player in enumerate(players, 1):
            name = player['first_name'] or f"Игрок {player['user_id']}"
            if player['username']:
                name = f"@{player['username']}"
            text += f"{i}. {name} - {player['value']:.2f}\n"
        await state.update_data({"top_field": field})
        await state.set_state(AdminStates.waiting_for_top_position)
        await callback.message.edit_text(text)
    
    @dp.message(AdminStates.waiting_for_top_position)
    async def admin_top_position(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            position = int(message.text.strip())
            if position < 1 or position > 10:
                await message.answer("❌ Позиция должна быть от 1 до 10")
                return
            data = await state.get_data()
            field = data.get("top_field")
            players, title = db.get_top_players_custom(field, 10)
            if position > len(players):
                await message.answer(f"❌ В топе только {len(players)} позиций")
                await state.clear()
                return
            player = players[position - 1]
            await state.update_data({"top_position": position, "top_current_user": player['user_id'], "top_current_value": player['value']})
            await state.set_state(AdminStates.waiting_for_top_user_id)
            await message.answer(
                f"✏️ <b>РЕДАКТИРОВАНИЕ ПОЗИЦИИ {position}</b>\n\n"
                f"Текущий игрок: {player['first_name']} (@{player['username'] or 'нет'})\n"
                f"Текущее значение: {player['value']:.2f}\n\n"
                f"Введи ID нового игрока для этой позиции:"
            )
        except ValueError:
            await message.answer("❌ Введи целое число")
    
    @dp.message(AdminStates.waiting_for_top_user_id)
    async def admin_top_new_user(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            new_user_id = int(message.text.strip())
            new_user = db.get_user(new_user_id)
            if not new_user:
                await message.answer("❌ Пользователь с таким ID не найден")
                return
            data = await state.get_data()
            field = data.get("top_field")
            position = data.get("top_position")
            current_user_id = data.get("top_current_user")
            await state.update_data({"new_user_id": new_user_id})
            await state.set_state(AdminStates.waiting_for_top_value)
            await message.answer(
                f"✏️ <b>НОВОЕ ЗНАЧЕНИЕ</b>\n\n"
                f"Позиция: {position}\n"
                f"Новый игрок: {new_user['first_name']} (@{new_user['username'] or 'нет'})\n"
                f"🆔 ID: {new_user_id}\n\n"
                f"Введи новое значение для этой позиции:"
            )
        except ValueError:
            await message.answer("❌ Введи корректный ID")
    
    @dp.message(AdminStates.waiting_for_top_value)
    async def admin_top_set_value(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        try:
            new_value = float(message.text.replace(',', '.'))
            if new_value < 0:
                await message.answer("❌ Значение не может быть отрицательным")
                return
            data = await state.get_data()
            field = data.get("top_field")
            position = data.get("top_position")
            new_user_id = data.get("new_user_id")
            if db.set_top_position(new_user_id, position, field, new_value):
                players, title = db.get_top_players_custom(field, 10)
                text = f"✅ <b>ТОП ОБНОВЛЕН!</b>\n{title}\n\n"
                for i, player in enumerate(players, 1):
                    name = player['first_name'] or f"Игрок {player['user_id']}"
                    if player['username']:
                        name = f"@{player['username']}"
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    text += f"{medal} {name}\n"
                    text += f"<blockquote>Значение: {player['value']:.2f}</blockquote>\n"
                    if i == position:
                        text += f"<blockquote>✨ НОВЫЙ ИГРОК</blockquote>\n"
                    text += "\n"
                await message.answer(text, reply_markup=get_main_keyboard(True))
            else:
                await message.answer("❌ Ошибка при обновлении топа")
            await state.clear()
        except ValueError:
            await message.answer("❌ Введи корректное число")
    
    # ========== АДМИН: УПРАВЛЕНИЕ PVP ТОПОМ ==========
    @dp.callback_query(lambda c: c.data == "admin_stats_pvp")
    async def admin_stats_pvp(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text("⚔️ <b>PVP ТОП ИГРОКОВ</b>\n\nВыбери по какому полю показать топ:", reply_markup=get_top_pvp_fields_keyboard())
    
    @dp.callback_query(lambda c: c.data.startswith('admin_top_pvp_view_'))
    async def admin_top_pvp_view(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        field = callback.data.replace('admin_top_pvp_view_', '')
        players, title = db.get_top_pvp_custom(field, 10)
        text = f"⚔️ <b>ТОП-10 ИГРОКОВ PVP</b>\n{title}\n\n"
        if players:
            for i, player in enumerate(players, 1):
                name = player['first_name'] or f"Игрок {player['user_id']}"
                if player['username']:
                    name = f"@{player['username']}"
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                text += f"{medal} {name}\n"
                text += f"<blockquote>Значение: {player['value']:.2f}</blockquote>\n"
                text += f"<blockquote>🆔 {player['user_id']}</blockquote>\n\n"
        else:
            text += "Пока нет данных для PvP топа."
        await callback.message.edit_text(text, reply_markup=get_top_pvp_actions_keyboard(field))
    
    @dp.callback_query(lambda c: c.data.startswith('admin_top_pvp_refresh_'))
    async def admin_top_pvp_refresh(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        field = callback.data.replace('admin_top_pvp_refresh_', '')
        players, title = db.get_top_pvp_custom(field, 10)
        text = f"⚔️ <b>ТОП-10 ИГРОКОВ PVP (обновлено)</b>\n{title}\n\n"
        if players:
            for i, player in enumerate(players, 1):
                name = player['first_name'] or f"Игрок {player['user_id']}"
                if player['username']:
                    name = f"@{player['username']}"
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                text += f"{medal} {name}\n"
                text += f"<blockquote>Значение: {player['value']:.2f}</blockquote>\n"
                text += f"<blockquote>🆔 {player['user_id']}</blockquote>\n\n"
        else:
            text += "Пока нет данных для PvP топа."
        await callback.message.edit_text(text, reply_markup=get_top_pvp_actions_keyboard(field))
    
    # ========== АДМИН: СБРОС ВСЕЙ СТАТИСТИКИ ==========
    @dp.callback_query(lambda c: c.data == "admin_stats_reset")
    async def admin_stats_reset(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await callback.message.edit_text(
            "⚠️ <b>СБРОС ВСЕЙ СТАТИСТИКИ ПРОЕКТА</b>\n\n"
            "Это действие удалит всю статистику всех игроков:\n"
            "• Оборот\n• Количество игр\n• Выигрыши\n• Винстрики\n• PvP статистику\n\n"
            "Балансы пользователей останутся нетронутыми.\n\n"
            "Ты уверен?",
            reply_markup=get_reset_stats_keyboard()
        )
    
    @dp.callback_query(lambda c: c.data == "admin_stats_reset_confirm")
    async def admin_stats_reset_confirm(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        if db.reset_all_stats():
            await callback.message.edit_text("✅ <b>Вся статистика проекта успешно сброшена!</b>\n\nТопы и статистика игроков обнулены.", reply_markup=get_main_keyboard(True))
        else:
            await callback.message.edit_text("❌ Ошибка при сбросе статистики")
    
    @dp.callback_query(lambda c: c.data == "admin_stats_project")
    async def admin_stats_project(callback: CallbackQuery):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        stats = db.get_project_stats()
        users_count = db.get_all_users_count()
        active_users = db.get_active_users_count(7)
        banned = len(db.get_banned_users())
        total_turnover, total_payouts = stats.get('total_turnover', 0), stats.get('total_payouts', 0)
        rtp = (total_payouts / total_turnover * 100) if total_turnover > 0 else 0
        fee = db.get_withdraw_fee() * 100
        text = f"""
📊 <b>ОБЩАЯ СТАТИСТИКА ПРОЕКТА</b>

👥 <b>Пользователи:</b>
<blockquote>Всего: {users_count}</blockquote>
<blockquote>Активных (7д): {active_users}</blockquote>
<blockquote>Забанено: {banned}</blockquote>

💰 <b>Финансы:</b>
<blockquote>Оборот: {format_number(total_turnover)}</blockquote>
<blockquote>Выплаты: {format_number(total_payouts)}</blockquote>
<blockquote>RTP: {rtp:.1f}%</blockquote>
<blockquote>Депозиты: {format_number(stats.get('total_deposits', 0))}</blockquote>
<blockquote>Выводы: {format_number(stats.get('total_withdrawals', 0))}</blockquote>
<blockquote>💸 Комиссия вывода: {fee:.0f}%</blockquote>

🎮 <b>Игры:</b>
<blockquote>Обычных игр: {stats.get('total_games', 0)}</blockquote>
<blockquote>PvP игр: {stats.get('total_pvp_games', 0)}</blockquote>

💎 <b>В среднем на игрока:</b>
<blockquote>Оборот: {format_number(total_turnover / users_count if users_count > 0 else 0)}</blockquote>
<blockquote>Игр: {stats.get('total_games', 0) / users_count if users_count > 0 else 0:.1f}</blockquote>"""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 ОБНОВИТЬ", callback_data="admin_stats_project"))
        builder.row(InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_stats_management"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    # ========== АДМИН: РАССЫЛКА ==========
    @dp.callback_query(lambda c: c.data == "admin_mailing")
    async def admin_mailing_start(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        await state.set_state(AdminStates.waiting_for_mailing_text)
        await callback.message.edit_text("📢 <b>РАССЫЛКА</b>\n\nВведи текст сообщения для рассылки всем пользователям:")
    
    @dp.message(AdminStates.waiting_for_mailing_text)
    async def admin_mailing_text(message: Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return
        text = message.text
        await state.update_data({"mailing_text": text})
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="✅ ОТПРАВИТЬ", callback_data="admin_mailing_confirm"),
                    InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="admin_mailing_cancel"))
        
        await message.answer(
            f"📢 <b>ПРЕДПРОСМОТР РАССЫЛКИ</b>\n\n{text}\n\nОтправить это сообщение всем пользователям?",
            reply_markup=builder.as_markup()
        )
    
    @dp.callback_query(lambda c: c.data == "admin_mailing_confirm")
    async def admin_mailing_confirm(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        if not is_admin(callback.from_user.id):
            return
        data = await state.get_data()
        text = data.get("mailing_text", "Нет текста")
        
        await callback.message.edit_text("📢 Рассылка началась... Это может занять некоторое время.")
        
        users = db.get_all_users_for_mailing()
        sent = 0
        failed = 0
        
        for user_id in users:
            try:
                await callback.bot.send_message(user_id, text)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await callback.message.edit_text(
            f"📢 <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
            f"✅ Успешно: {sent}\n"
            f"❌ Не удалось: {failed}",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
    
    @dp.callback_query(lambda c: c.data == "admin_mailing_cancel")
    async def admin_mailing_cancel(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await callback.message.edit_text("❌ Рассылка отменена", reply_markup=get_admin_keyboard())