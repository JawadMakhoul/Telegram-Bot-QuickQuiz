from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Define a simple start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}, I am your bot!")

# Main function to run the bot
def main():
    # Replace 'YOUR_TOKEN' with your bot's API token from BotFather
    application = ApplicationBuilder().token("7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()