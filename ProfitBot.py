import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Get bot token from Railway environment variables
TOKEN = os.getenv("TOKEN")

# Initialize the application
app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the bot starts."""
    await update.message.reply_text(
        "Hello! Send me an amount, and I'll calculate your Fiverr net profit after fees.\n\n"
        "Example: If you send '100', I'll tell you how much you keep after Fiverr's fees."
    )

async def calculate_profit(update: Update, context: CallbackContext) -> None:
    """Calculate net profit after Fiverr fees."""
    try:
        user_input = update.message.text.strip()
        total_amount = float(user_input)

        # Fiverr fee calculations
        amount_after_20 = total_amount * 0.80  # Deduct 20%
        final_profit = amount_after_20 * 0.60  # Deduct 40% from the remaining

        await update.message.reply_text(
            f"For ${total_amount}, your net profit after Fiverr fees is: **${final_profit:.2f}**"
        )
    except ValueError:
        await update.message.reply_text("Please send a valid number (e.g., 100, 250.50).")

def main():
    """Start the bot."""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_profit))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
