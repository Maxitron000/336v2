async def main():
    """Основная функция для запуска бота"""
    try:
        # Инициализация базы данных
        db = DatabaseService()

        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()

        # Удаляем меню команд
        await application.bot.delete_my_commands()
        
        # Убираем кнопку меню
        await application.bot.set_my_commands([])

        # Инициализация хэндлера
        bot_handler = BotHandler(db)

        # Регистрация хэндлеров
        application.add_handler(CommandHandler("start", bot_handler.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_message))
        application.add_handler(CallbackQueryHandler(bot_handler.handle_callback))

        # Запуск бота
        print("🤖 Бот запущен и готов к работе...")
        await application.run_polling()
    except Exception as e:
        print(f"An error occurred: {e}")