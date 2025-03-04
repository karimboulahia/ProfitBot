import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Get bot token from environment
TOKEN = os.getenv("TOKEN")

# Connect to SQLite database
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT,
    budget REAL,
    deadline TEXT,
    status TEXT DEFAULT "Active"
)
''')
conn.commit()

# Define conversation states
CLIENT_NAME, BUDGET, DEADLINE, FILTER_STATUS = range(4)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💰 Karim Mode", callback_data="karim_mode")],
        [InlineKeyboardButton("📑 Manage Orders", callback_data="manage_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

# --- Manage Orders Menu ---
async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Add Order", callback_data="add_order")],
        [InlineKeyboardButton("📋 View Orders", callback_data="view_orders")],
        [InlineKeyboardButton("🔄 Filter by Status", callback_data="filter_status")],
        [InlineKeyboardButton("✏️ Change Order Status", callback_data="change_status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📑 Manage your orders:", reply_markup=reply_markup)

# --- Add New Order ---
async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter the **Client Name**:")
    return CLIENT_NAME

async def get_client_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["client_name"] = update.message.text
    await update.message.reply_text("Enter the **Budget ($)**:")
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        budget = float(update.message.text)
        context.user_data["budget"] = budget
        await update.message.reply_text("Enter the **Deadline (YYYY-MM-DD)**:")
        return DEADLINE
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the budget:")
        return BUDGET

async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["deadline"] = update.message.text
    cursor.execute("INSERT INTO orders (client_name, budget, deadline) VALUES (?, ?, ?)",
                   (context.user_data["client_name"], context.user_data["budget"], context.user_data["deadline"]))
    conn.commit()
    await update.message.reply_text("✅ Order Added Successfully!")
    return ConversationHandler.END

# --- View Orders ---
async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT id, client_name, budget, deadline, status FROM orders")
    orders = cursor.fetchall()

    if not orders:
        await update.callback_query.message.reply_text("No orders found.")
        return

    order_text = "\n".join([f"🆔 {o[0]} | {o[1]} | ${o[2]:.2f} | Deadline: {o[3]} | Status: {o[4]}" for o in orders])
    await update.callback_query.message.reply_text(f"📋 Orders:\n\n{order_text}")

# --- Filter Orders by Status ---
async def filter_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🟢 Active", callback_data="status_Active")],
        [InlineKeyboardButton("🟡 In Progress", callback_data="status_In Progress")],
        [InlineKeyboardButton("🔴 Completed", callback_data="status_Completed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Choose the status to filter by:", reply_markup=reply_markup)
    return FILTER_STATUS

async def filter_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status = update.callback_query.data.split("_")[1]
    cursor.execute("SELECT id, client_name, budget, deadline FROM orders WHERE status = ?", (status,))
    orders = cursor.fetchall()

    if not orders:
        await update.callback_query.message.reply_text(f"No orders found for status: {status}.")
        return

    order_text = "\n".join([f"🆔 {o[0]} | {o[1]} | ${o[2]:.2f} | Deadline: {o[3]}" for o in orders])
    await update.callback_query.message.reply_text(f"📋 Orders with status '{status}':\n\n{order_text}")

# --- Change Order Status ---
async def change_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter Order ID to change status:")
    return ConversationHandler.END

async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    order_id = update.message.text
    keyboard = [
        [InlineKeyboardButton("🟢 Active", callback_data=f"update_Active_{order_id}")],
        [InlineKeyboardButton("🟡 In Progress", callback_data=f"update_In Progress_{order_id}")],
        [InlineKeyboardButton("🔴 Completed", callback_data=f"update_Completed_{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose new status:", reply_markup=reply_markup)

async def confirm_update_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.callback_query.data.split("_")
    new_status, order_id = data[1], data[2]

    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    await update.callback_query.message.reply_text(f"✅ Order {order_id} status updated to '{new_status}'!")

# --- Main Bot Setup ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(manage_orders, pattern="manage_orders"))
    app.add_handler(CallbackQueryHandler(view_orders, pattern="view_orders"))
    app.add_handler(CallbackQueryHandler(filter_status, pattern="filter_status"))
    app.add_handler(CallbackQueryHandler(filter_orders, pattern="status_"))
    app.add_handler(CallbackQueryHandler(change_status, pattern="change_status"))
    app.add_handler(CallbackQueryHandler(confirm_update_status, pattern="update_"))

    order_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_order, pattern="add_order")],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            FILTER_STATUS: [CallbackQueryHandler(filter_orders, pattern="status_")]
        },
        fallbacks=[]
    )

    app.add_handler(order_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
