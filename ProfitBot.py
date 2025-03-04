import os
import sqlite3
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
    user_id INTEGER,
    client_name TEXT,
    budget REAL,
    deadline TEXT,
    status TEXT DEFAULT "Active"
)
''')
conn.commit()

# Define conversation states
CLIENT_NAME, BUDGET, DEADLINE, ORDER_ID, FILTER_STATUS = range(5)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💰 Karim Mode", callback_data="karim_mode")],
        [InlineKeyboardButton("📑 Manage Orders", callback_data="manage_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

# --- Karim Mode ---
async def karim_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["karim_mode"] = True  # Mark Karim Mode as active
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("💰 Send me an amount, and I'll calculate your Fiverr net profit.")

async def calculate_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("adding_order") or context.user_data.get("deleting_order") or context.user_data.get("filtering_orders"):
        return  # Ignore if user is performing an order-related action

    try:
        total_amount = float(update.message.text.strip())
        amount_after_20 = total_amount * 0.80
        final_profit = amount_after_20 * 0.60
        await update.message.reply_text(f"For ${total_amount}, your net profit after Fiverr fees is: **${final_profit:.2f}**")
    except ValueError:
        await update.message.reply_text("Please send a valid number (e.g., 100, 250.50).")

# --- Manage Orders Menu ---
async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Add Order", callback_data="add_order")],
        [InlineKeyboardButton("📋 View My Orders", callback_data="view_orders")],
        [InlineKeyboardButton("🔄 Filter Orders by Status", callback_data="filter_orders")],
        [InlineKeyboardButton("❌ Delete My Order", callback_data="delete_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📑 Manage your orders:", reply_markup=reply_markup)

# --- Add New Order ---
async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["adding_order"] = True
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter the **Client Name**:")
    return CLIENT_NAME

async def get_client_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["client_name"] = update.message.text
    await update.message.reply_text("Enter the **Budget ($)** (e.g., 50):")
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        budget = float(update.message.text)
        context.user_data["budget"] = budget
        await update.message.reply_text("Enter the **Deadline (YYYY-MM-DD)**:")
        return DEADLINE
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number for the budget (e.g., 50).")
        return BUDGET

async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.chat_id
    context.user_data["deadline"] = update.message.text
    cursor.execute("INSERT INTO orders (user_id, client_name, budget, deadline) VALUES (?, ?, ?, ?)",
                   (user_id, context.user_data["client_name"], context.user_data["budget"], context.user_data["deadline"]))
    conn.commit()

    context.user_data["adding_order"] = False
    await update.message.reply_text("✅ Order Added Successfully!")
    return ConversationHandler.END

# --- View Only the User's Orders ---
async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.message.chat_id
    cursor.execute("SELECT id, client_name, budget, deadline, status FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()

    if not orders:
        await update.callback_query.message.reply_text("No orders found.")
        return

    order_text = "\n".join([f"🆔 {o[0]} | {o[1]} | ${o[2]:.2f} | Deadline: {o[3]} | Status: {o[4]}" for o in orders])
    await update.callback_query.message.reply_text(f"📋 Your Orders:\n\n{order_text}")

# --- Filter Orders by Status ---
async def filter_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🟢 Active", callback_data="status_Active")],
        [InlineKeyboardButton("🟡 In Progress", callback_data="status_In Progress")],
        [InlineKeyboardButton("🔴 Completed", callback_data="status_Completed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data["filtering_orders"] = True
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Select a status to filter:", reply_markup=reply_markup)
    return FILTER_STATUS

async def filter_orders_by_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.message.chat_id
    status = update.callback_query.data.split("_")[1]
    cursor.execute("SELECT id, client_name, budget, deadline FROM orders WHERE user_id = ? AND status = ?", (user_id, status))
    orders = cursor.fetchall()

    context.user_data["filtering_orders"] = False

    if not orders:
        await update.callback_query.message.reply_text(f"No orders found with status: {status}.")
        return

    order_text = "\n".join([f"🆔 {o[0]} | {o[1]} | ${o[2]:.2f} | Deadline: {o[3]}" for o in orders])
    await update.callback_query.message.reply_text(f"📋 Your Orders with status '{status}':\n\n{order_text}")

# --- Delete Order ---
async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["deleting_order"] = True
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter the **Order ID** to delete:")
    return ORDER_ID

async def confirm_delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.chat_id
    order_id = update.message.text

    cursor.execute("DELETE FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
    conn.commit()

    context.user_data["deleting_order"] = False
    await update.message.reply_text(f"✅ Order {order_id} deleted successfully!")
    return ConversationHandler.END

# --- Main Bot Setup ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(karim_mode, pattern="karim_mode"))
    app.add_handler(CallbackQueryHandler(manage_orders, pattern="manage_orders"))
    app.add_handler(CallbackQueryHandler(view_orders, pattern="view_orders"))
    app.add_handler(CallbackQueryHandler(filter_orders, pattern="filter_orders"))
    app.add_handler(CallbackQueryHandler(filter_orders_by_status, pattern="status_"))
    app.add_handler(CallbackQueryHandler(delete_order, pattern="delete_order"))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
