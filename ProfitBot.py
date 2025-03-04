from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext


# Replace this with your Telegram Bot Token
TOKEN = "8070911062:AAGRIeT4hZbc8MMqZyTyuk7DfuNo--KAVSY"

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message and explain how to use the bot."""
    update.message.reply_text(
        "Hello! Send me an amount, and I'll calculate your Fiverr net profit after fees.\n\n"
        "Example: If you send '100', I'll tell you how much you keep after Fiverr's fees."
    )

def calculate_profit(update: Update, context: CallbackContext) -> None:
    """Calculate net profit after Fiverr fees."""
    try:
        user_input = update.message.text.strip()
        total_amount = float(user_input)

        # Fiverr fee calculations
        amount_after_20 = total_amount * 0.80  # Deduct 20%
        final_profit = amount_after_20 * 0.60  # Deduct 40% from the remaining

        update.message.reply_text(
            f"For ${total_amount}, your net profit after Fiverr fees is: **${final_profit:.2f}**"
        )
    except ValueError:
        update.message.reply_text("Please send a valid number (e.g., 10, 25.50).")

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler("start", start))

    # Messages (for numbers input)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, calculate_profit))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

