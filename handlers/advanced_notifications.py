
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.db_service import DatabaseService
from datetime import datetime, timedelta
import logging
import asyncio

router = Router()
db = DatabaseService()

class NotificationStates(StatesGroup):
    waiting_for_custom_message = State()
    waiting_for_schedule_time = State()

class SmartNotificationSystem:
    def __init__(self):
        self.db = DatabaseService()
        self.active_alerts = {}
        
    async def check_suspicious_patterns(self):
        """Проверка подозрительных паттернов"""
        alerts = []
        
        # Проверяем частые отлучки одного бойца
        records = self.db.get_all_records(days=7)
        user_departures = {}
        
        for record in records:
            if record['action'] == 'не в части':
                name = record['full_name']
                user_departures[name] = user_departures.get(name, 0) + 1
        
        for name, count in user_departures.items():
            if count > 10:  # Более 10 отлучек за неделю
                alerts.append({
                    'type': 'frequent_departures',
                    'user': name,
                    'count': count,
                    'message': f"⚠️ {name} имеет {count} отлучек за неделю"
                })
        
        # Проверяем длительные отсутствия
        current_status = self.db.get_current_status()
        for user in current_status.get('absent_users', []):
            # Ищем последнюю отметку "в части"
            last_present = self.db.get_last_present_record(user['user_id'])
            if last_present:
                last_time = datetime.fromisoformat(last_present['timestamp'].replace('Z', '+00:00'))
                hours_absent = (datetime.now() - last_time).total_seconds() / 3600
                
                if hours_absent > 24:  # Отсутствует более суток
                    alerts.append({
                        'type': 'long_absence',
                        'user': user['name'],
                        'hours': int(hours_absent),
                        'location': user['location'],
                        'message': f"🚨 {user['name']} отсутствует {int(hours_absent)} часов ({user['location']})"
                    })
        
        return alerts
    
    async def send_smart_alerts(self, bot):
        """Отправка умных уведомлений"""
        try:
            alerts = await self.check_suspicious_patterns()
            
            if alerts:
                text = "🔍 **Анализ активности выявил:**\n\n"
                for alert in alerts:
                    text += f"• {alert['message']}\n"
                
                # Отправляем только главному админу
                from config import MAIN_ADMIN_ID
                await bot.send_message(MAIN_ADMIN_ID, text, parse_mode="Markdown")
                
        except Exception as e:
            logging.error(f"Ошибка умных уведомлений: {e}")

# Глобальный экземпляр системы
smart_notifications = SmartNotificationSystem()

def get_notification_management_keyboard():
    """Клавиатура управления уведомлениями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Рассылка всем", callback_data="notify_broadcast"),
            InlineKeyboardButton(text="🎯 Выборочная рассылка", callback_data="notify_selective")
        ],
        [
            InlineKeyboardButton(text="⏰ Отложенная рассылка", callback_data="notify_scheduled"),
            InlineKeyboardButton(text="🚨 Экстренное уведомление", callback_data="notify_emergency")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика рассылок", callback_data="notify_stats"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="notify_settings")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

@router.callback_query(F.data == "admin_notifications_advanced")
async def callback_advanced_notifications(callback: CallbackQuery):
    """Расширенные уведомления"""
    user_id = callback.from_user.id
    
    # Проверка прав админа
    from handlers.admin import is_admin
    if not await is_admin(user_id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 **Расширенная система уведомлений**\n\n"
        "🎯 Возможности:\n"
        "• Массовые рассылки всем пользователям\n"
        "• Выборочные уведомления по группам\n"
        "• Отложенные сообщения по расписанию\n"
        "• Экстренные уведомления\n"
        "• Аналитика доставки\n\n"
        "Выберите нужное действие:",
        reply_markup=get_notification_management_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "notify_broadcast")
async def callback_notify_broadcast(callback: CallbackQuery, state: FSMContext):
    """Рассылка всем пользователям"""
    await state.set_state(NotificationStates.waiting_for_custom_message)
    await callback.message.edit_text(
        "📢 **Массовая рассылка**\n\n"
        "Введите текст сообщения для отправки всем зарегистрированным пользователям:\n\n"
        "💡 Поддерживается Markdown форматирование\n"
        "⚠️ Сообщение будет доставлено всем без исключения",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_notifications_advanced")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(NotificationStates.waiting_for_custom_message)
async def handle_custom_message(message: Message, state: FSMContext):
    """Обработка пользовательского сообщения для рассылки"""
    custom_text = message.text.strip()
    
    if len(custom_text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (максимум 1000 символов)")
        return
    
    # Получаем всех пользователей
    users = db.get_all_users()
    
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_notifications_advanced")
        ]
    ]
    
    await state.update_data(broadcast_text=custom_text)
    await message.answer(
        f"📢 **Подтверждение рассылки**\n\n"
        f"**Текст сообщения:**\n{custom_text}\n\n"
        f"👥 **Получателей:** {len(users)}\n\n"
        f"⚠️ Подтвердите отправку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "confirm_broadcast")
async def callback_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение рассылки"""
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text')
    
    if not broadcast_text:
        await callback.answer("❌ Текст сообщения потерян", show_alert=True)
        return
    
    users = db.get_all_users()
    sent_count = 0
    failed_count = 0
    
    await callback.message.edit_text("🔄 Выполняется рассылка...", parse_mode="Markdown")
    
    for user in users:
        try:
            await callback.bot.send_message(
                user['id'],
                f"📢 **Сообщение от администрации:**\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            sent_count += 1
            
            # Небольшая задержка для избежания лимитов
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed_count += 1
            logging.error(f"Ошибка отправки пользователю {user['id']}: {e}")
    
    await state.clear()
    
    result_text = f"📊 **Результаты рассылки:**\n\n"
    result_text += f"✅ Доставлено: {sent_count}\n"
    result_text += f"❌ Ошибок: {failed_count}\n"
    result_text += f"👥 Всего пользователей: {len(users)}\n\n"
    result_text += f"📈 Успешность: {(sent_count/len(users)*100):.1f}%"
    
    await callback.message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notifications_advanced")]
        ]),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "notify_emergency")
async def callback_notify_emergency(callback: CallbackQuery):
    """Экстренные уведомления"""
    emergency_templates = [
        "🚨 ВНИМАНИЕ! Экстренный сбор всего личного состава!",
        "⚠️ ТРЕВОГА! Всем немедленно явиться в расположение части!",
        "🔴 СРОЧНО! Отменяются все увольнения. Возвращаться в часть!",
        "📢 ВАЖНО! Проверка личного состава через 30 минут!",
        "🚁 УЧЕНИЕ! Всем собраться в казарме в течение 15 минут!"
    ]
    
    keyboard = []
    for i, template in enumerate(emergency_templates):
        short_text = template[:30] + "..." if len(template) > 30 else template
        keyboard.append([InlineKeyboardButton(
            text=short_text, 
            callback_data=f"emergency_template_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="📝 Свой текст", callback_data="emergency_custom")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notifications_advanced")])
    
    await callback.message.edit_text(
        "🚨 **Экстренные уведомления**\n\n"
        "⚠️ Выберите шаблон или введите свой текст:\n\n"
        "💡 Экстренные сообщения отправляются всем мгновенно",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("emergency_template_"))
async def callback_emergency_template(callback: CallbackQuery):
    """Отправка экстренного уведомления по шаблону"""
    template_index = int(callback.data.split("_")[-1])
    
    emergency_templates = [
        "🚨 ВНИМАНИЕ! Экстренный сбор всего личного состава!",
        "⚠️ ТРЕВОГА! Всем немедленно явиться в расположение части!",
        "🔴 СРОЧНО! Отменяются все увольнения. Возвращаться в часть!",
        "📢 ВАЖНО! Проверка личного состава через 30 минут!",
        "🚁 УЧЕНИЕ! Всем собраться в казарме в течение 15 минут!"
    ]
    
    message_text = emergency_templates[template_index]
    
    keyboard = [
        [
            InlineKeyboardButton(text="🚨 ОТПРАВИТЬ ВСЕМ", callback_data=f"send_emergency_{template_index}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="notify_emergency")
        ]
    ]
    
    await callback.message.edit_text(
        f"🚨 **ЭКСТРЕННОЕ УВЕДОМЛЕНИЕ**\n\n"
        f"**Текст:**\n{message_text}\n\n"
        f"⚠️ **ВНИМАНИЕ!** Сообщение будет отправлено ВСЕМ пользователям немедленно!\n\n"
        f"Подтвердите отправку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("send_emergency_"))
async def callback_send_emergency(callback: CallbackQuery):
    """Отправка экстренного сообщения"""
    template_index = int(callback.data.split("_")[-1])
    
    emergency_templates = [
        "🚨 ВНИМАНИЕ! Экстренный сбор всего личного состава!",
        "⚠️ ТРЕВОГА! Всем немедленно явиться в расположение части!",
        "🔴 СРОЧНО! Отменяются все увольнения. Возвращаться в часть!",
        "📢 ВАЖНО! Проверка личного состава через 30 минут!",
        "🚁 УЧЕНИЕ! Всем собраться в казарме в течение 15 минут!"
    ]
    
    message_text = emergency_templates[template_index]
    users = db.get_all_users()
    
    await callback.message.edit_text("🚨 ОТПРАВКА ЭКСТРЕННОГО УВЕДОМЛЕНИЯ...", parse_mode="Markdown")
    
    sent_count = 0
    for user in users:
        try:
            await callback.bot.send_message(
                user['id'],
                f"🚨 **ЭКСТРЕННОЕ СООБЩЕНИЕ**\n\n{message_text}\n\n⏰ {datetime.now().strftime('%H:%M')}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            logging.error(f"Ошибка экстренной отправки пользователю {user['id']}: {e}")
    
    await callback.message.edit_text(
        f"🚨 **ЭКСТРЕННОЕ УВЕДОМЛЕНИЕ ОТПРАВЛЕНО**\n\n"
        f"✅ Доставлено: {sent_count}/{len(users)}\n"
        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notifications_advanced")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer("✅ Экстренное уведомление отправлено!", show_alert=True)
