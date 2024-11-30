import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from Token import TOKEN  # Импортируем токен из Token.py

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

ASK_NAME, ASK_SURNAME, ASK_CLASS, GET_FEEDBACK, ANONYMOUS_FEEDBACK, ADMIN_FEEDBACK = range(6)

# Словарь для хранения сообщений пользователей
user_feedback = {}

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ["Новый пост"],
        ["Обращение к админу"],
        ["Мои посты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Здравствуйте! Выберите действие:', reply_markup=reply_markup)

# Обработчик для "Новый пост"
def new_post(update: Update, context: CallbackContext) -> int:
    context.user_data['post_type'] = 'Новый пост'
    update.message.reply_text('Пожалуйста, введите ваше имя. Если не хотите оставлять свое имя, напишите "анонимно".')
    return ASK_NAME

# Обработчик для "Обращение к админу"
def contact_admin(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Пожалуйста, введите ваше сообщение для администратора.')
    return ADMIN_FEEDBACK

# Обработчик для получения имени пользователя
def ask_name(update: Update, context: CallbackContext) -> int:
    user_name = update.message.text
    if user_name.lower() == 'анонимно':
        context.user_data['name'] = 'Anonymous'
        context.user_data['surname'] = 'Anonymous'
        context.user_data['class'] = 'Anonymous'
        update.message.reply_text('Отлично! Теперь отправьте ваше сообщение.')
        return ANONYMOUS_FEEDBACK
    else:
        context.user_data['name'] = user_name
        update.message.reply_text('Спасибо! Теперь введите вашу фамилию.')
        return ASK_SURNAME

# Обработчик для получения фамилии пользователя
def ask_surname(update: Update, context: CallbackContext) -> int:
    user_surname = update.message.text
    context.user_data['surname'] = user_surname
    update.message.reply_text('Отлично! Теперь введите ваш класс.')
    return ASK_CLASS

# Обработчик для получения класса пользователя
def ask_class(update: Update, context: CallbackContext) -> int:
    context.user_data['class'] = update.message.text
    update.message.reply_text('Спасибо! Теперь отправьте ваше сообщение.')
    return GET_FEEDBACK

# Обработчик для получения обратной связи
def get_feedback(update: Update, context: CallbackContext) -> int:
    user_message = update.message.text
    user_name = context.user_data['name']
    user_surname = context.user_data['surname']
    user_class = context.user_data['class']
    post_type = context.user_data['post_type']
    user_id = update.message.from_user.id
    
    feedback_entry = f"User ID: {user_id}, Type: {post_type}, User: {user_name} {user_surname}, Class: {user_class}, Message: {user_message}\n"
    
    # Сохранение в файл
    with open('feedback.txt', 'a', encoding='utf-8') as f:
        f.write(feedback_entry)
    
    # Сохранение в словарь
    if user_id not in user_feedback:
        user_feedback[user_id] = []
    user_feedback[user_id].append(feedback_entry)
    
    update.message.reply_text('Ваше сообщение сохранено!')
    return ConversationHandler.END

# Обработчик для получения обратной связи анонимного пользователя
def anonymous_feedback(update: Update, context: CallbackContext) -> int:
    user_message = update.message.text
    post_type = context.user_data['post_type']
    user_id = update.message.from_user.id
    
    feedback_entry = f"User ID: {user_id}, Type: {post_type}, User: Anonymous, Message: {user_message}\n"
    
    # Сохранение в файл
    with open('feedback.txt', 'a', encoding='utf-8') as f:
        f.write(feedback_entry)
    
    # Сохранение в словарь
    if user_id not in user_feedback:
        user_feedback[user_id] = []
    user_feedback[user_id].append(feedback_entry)
    
    update.message.reply_text('Ваше сообщение сохранено!')
    return ConversationHandler.END

# Обработчик для получения сообщений для администратора
def admin_feedback(update: Update, context: CallbackContext) -> int:
    user_message = update.message.text
    user_id = update.message.from_user.id  # Получаем ID пользователя
    
    feedback_entry = f"User ID: {user_id}, Message: {user_message}\n"
    
    # Логирование сообщения для администратора
    logger.info(f"Admin message from user {user_id}: {user_message}")
    
    # Сохранение в файл
    with open('admin_feedback.txt', 'a', encoding='utf-8') as f:
        f.write(feedback_entry)
    
    update.message.reply_text('Ваше сообщение для администратора сохранено!')
    return ConversationHandler.END

# Обработчик команды /view
def view_feedback(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_feedback and user_feedback[user_id]:
        feedback_list = user_feedback[user_id]
        response = "Ваши сообщения:\n" + "\n".join(feedback_list)
        update.message.reply_text(response)
    else:
        update.message.reply_text("У вас пока нет сохраненных сообщений.")

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Процесс отменен.')
    return ConversationHandler.END

def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Новый пост$'), new_post)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_name)],
            ASK_SURNAME: [MessageHandler(Filters.text & ~Filters.command, ask_surname)],
            ASK_CLASS: [MessageHandler(Filters.text & ~Filters.command, ask_class)],
            GET_FEEDBACK: [MessageHandler(Filters.text & ~Filters.command, get_feedback)],
            ANONYMOUS_FEEDBACK: [MessageHandler(Filters.text & ~Filters.command, anonymous_feedback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    admin_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Обращение к админу$'), contact_admin)],
        states={
            ADMIN_FEEDBACK: [MessageHandler(Filters.text & ~Filters.command, admin_feedback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Регистрируем обработчики команд и сообщений
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(admin_conv_handler)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('view', view_feedback))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Мои посты$'), view_feedback))

    # Запуск бота
    updater.start_polling()

    # Работает до нажатия Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
