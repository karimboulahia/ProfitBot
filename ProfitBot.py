import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Initialize the bot token
TOKEN = os.getenv("TOKEN")

# Initialize database
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT,
    deadline TEXT,
    budget REAL,
    status TEXT
)
''')
conn.commit()

# Define conversation states
CLIENT_NAME, DEADLINE, BUDGET, EDIT_ORDER, CHANGE_STATUS, DELETE_ORDER, SEARCH_ORDER = range(7)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💰 Karim Mode", callback_data="karim_mode")],
        [InlineKeyboardButton("📑 Add Orders", callback_data="add_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

# --- Karim Mode (Fiverr Net Profit Calculation) ---
async def karim_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("💰 Karim Mode activated! Send me an amount, and I'll calculate your Fiverr net profit.")

async def calculate_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_input = update.message.text.strip()
        total_amount = float(user_input)
        amount_after_20 = total_amount * 0.80
        final_profit = amount_after_20 * 0.60
        await update.message.reply_text(f"For ${total_amount}, your net profit after Fiverr fees is: **${final_profit:.2f}**")
    except ValueError:
        await update.message.reply_text("Please send a valid number (e.g., 100, 250.50).")

# --- Order Management ---
async def add_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Add Order", callback_data="add_order")],
        [InlineKeyboardButton("✏️ Edit Order", callback_data="edit_order")],
        [InlineKeyboardButton("🔄 Change Order Status", callback_data="change_status")],
        [InlineKeyboardButton("📋 View Active Orders", callback_data="view_orders")],
        [InlineKeyboardButton("💵 Calculate Earnings", callback_data="calculate_earnings")],
        [InlineKeyboardButton("🔍 Search Orders", callback_data="search_orders")],
        [InlineKeyboardButton("📅 View by Deadline", callback_data="view_by_deadline")],
        [InlineKeyboardButton("⏳ Overdue Orders", callback_data="overdue_orders")],
        [InlineKeyboardButton("❌ Delete Order", callback_data="delete_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📑 Manage your orders:", reply_markup=reply_markup)

# --- Add New Order ---
async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter Client Name:")
    return CLIENT_NAME

async def get_client_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["client_name"] = update.message.text
    await update.message.reply_text("Enter Deadline (YYYY-MM-DD):")
    return DEADLINE

async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["deadline"] = update.message.text
    await update.message.reply_text("Enter Budget ($):")
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cursor.execute("INSERT INTO orders (client_name, deadline, budget, status) VALUES (?, ?, ?, ?)",
                   (context.user_data["client_name"], context.user_data["deadline"], float(update.message.text), "Active"))
    conn.commit()
    await update.message.reply_text("✅ Order Added Successfully!")
    return ConversationHandler.END

# --- View Orders ---
async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT id, client_name, deadline, budget, status FROM orders WHERE status='Active'")
    orders = cursor.fetchall()
    text = "\n".join([f"🆔 {o[0]} | {o[1]} | {o[2]} | ${o[3]} | {o[4]}" for o in orders]) if orders else "No active orders."
    await update.callback_query.message.reply_text(f"📋 Active Orders:\n\n{text}")

# --- Search Orders ---
async def search_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter Client Name to Search:")
    return SEARCH_ORDER

async def get_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client_name = update.message.text
    cursor.execute("SELECT id, deadline, budget, status FROM orders WHERE client_name LIKE ?", ('%' + client_name + '%',))
    orders = cursor.fetchall()
    text = "\n".join([f"🆔 {o[0]} | Deadline: {o[1]} | ${o[2]} | {o[3]}" for o in orders]) if orders else f"No orders found for '{client_name}'."
    await update.message.reply_text(f"📋 Orders for {client_name}:\n\n{text}")
    return ConversationHandler.END

# --- Calculate Earnings ---
async def calculate_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT SUM(budget) FROM orders WHERE status='Completed' AND strftime('%Y-%m', deadline) = strftime('%Y-%m', 'now')")
    total_earnings = cursor.fetchone()[0] or 0
    await update.callback_query.message.reply_text(f"💵 Total Earnings This Month: ${total_earnings:.2f}")

# --- Main Bot Setup ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_profit))

    app.add_handler(CallbackQueryHandler(karim_mode, pattern="karim_mode"))
    app.add_handler(CallbackQueryHandler(add_orders, pattern="add_orders"))
    app.add_handler(CallbackQueryHandler(view_orders, pattern="view_orders"))
    app.add_handler(CallbackQueryHandler(calculate_earnings, pattern="calculate_earnings"))
    app.add_handler(CallbackQueryHandler(search_orders, pattern="search_orders"))

    order_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_order, pattern="add_order")],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            SEARCH_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_search_results)]
        },
        fallbacks=[]
    )
    app.add_handler(order_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
