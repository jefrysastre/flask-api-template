from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os.path


class TelegramBotNotification:
    def __init__(self, bot_token, chats, log_file='logs/app'):
        self.bot_token = bot_token
        self.chats = chats
        self.log_file = log_file

        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        self.updater = Updater(self.bot_token)

        # Get the dispatcher to register handlers
        self.dispatcher = self.updater.dispatcher

        # on different commands - answer in Telegram
        self.dispatcher.add_handler(CommandHandler("log", self.generate_log_method()))
        self.dispatcher.add_handler(CommandHandler("get_id", self.generate_get_id_method()))

        # Start the Bot
        self.updater.start_polling()

    def send(self, message, chat_name="default"):
        _chat_id = self.chats[chat_name]
        self.updater.bot.send_message(
            chat_id=_chat_id,
            text=message
        )

    # Define a few command handlers. These usually take the two arguments bot and
    # update. Error handlers also receive the raised TelegramError object in error.
    def generate_log_method(self):

        def log_handler(update, context):
            """Send a message when the command /status is issued."""
            # update.message.reply_text('Service is up and running')

            _log_file = self.log_file

            if os.path.isfile(_log_file):
                update.send_message(
                    chat_id=context.message.chat_id,
                    text='Sending log file ...'
                )
                update.send_document(
                    chat_id=context.message.chat_id,
                    document=open(_log_file, 'rb')
                )
            else:
                update.send_message(
                    chat_id=context.message.chat_id,
                    text='Log not found at {0}'.format(_log_file)
                )
        return log_handler

    def generate_get_id_method(self):
        def get_id_handler(update, context):
            update.send_message(
                chat_id=context.message.chat_id,
                text='{0}: Type: {1} Id: {2}'.format(
                    context.message.chat.first_name,
                    context.message.chat.type,
                    context.message.chat_id
                )
            )
        return get_id_handler

    @staticmethod
    def echo(update, context):
        """Echo the user message."""
        context.message.reply_text("Recebido: " + context.message.text)

    def error(update, context):
        """Log Errors caused by Updates."""
        # logger.warning('Update "%s" caused error "%s"', update, context.error)
        print('Update "%s" caused error "%s"', update, context.error)

