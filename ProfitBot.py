import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Get bot token from environment
TOKEN = os.getenv("TOKEN")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💰 Welcome to Karim Mode! Send me an amount, and I'll calculate your Fiverr net profit.")

# --- Calculate Fiverr Net Profit ---
async def calculate_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        total_amount = float(update.message.text.strip())
        amount_after_20 = total_amount * 0.80  # Fiverr takes 20%
        final_profit = amount_after_20 * 0.60  # 40% Cash Advance
        await update.message.reply_text(f"For ${total_amount}, your net profit after Fiverr fees and cash advance is: **${final_profit:.2f}**")
    except ValueError:
        await update.message.reply_text("⚠️ Please send a valid number (e.g., 100, 250.50).")

# --- Main Bot Setup ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_profit))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
