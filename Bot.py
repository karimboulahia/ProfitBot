import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, filters

# Get bot token from Railway environment variables
TOKEN = os.getenv("TOKEN")

# Initialize the Telegram bot
app = ApplicationBuilder().token(TOKEN).build()

# Restricted Fiverr username
RESTRICTED_USERNAME = "karim_boulahia"

### **1️⃣ Fiverr Profile Analyzer**
async def analyze(update: Update, context: CallbackContext) -> None:
    """Fetch Fiverr profile details and provide ranking advice."""
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /analyze FiverrUsername")
        return

    fiverr_username = context.args[0]

    # Restrict analysis for specific account
    if fiverr_username.lower() == RESTRICTED_USERNAME.lower():
        await update.message.reply_text("❌ This Fiverr account cannot be analyzed.")
        return

    profile_url = f"https://www.fiverr.com/{fiverr_username}"

    try:
        # Fetch Fiverr profile page
        response = requests.get(profile_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract Fiverr profile details
        rating_element = soup.find("span", class_="rating-score")
        orders_element = soup.find("strong", class_="total-orders")
        gig_title_element = soup.find("h3", class_="gig-title")

        rating = rating_element.text.strip() if rating_element else "N/A"
        orders = orders_element.text.strip() if orders_element else "N/A"
        gig_title = gig_title_element.text.strip() if gig_title_element else "N/A"

        # Ranking advice based on extracted data
        advice = "📢 **Advice for Improvement:**\n"

        if rating != "N/A":
            rating_float = float(rating)
            if rating_float >= 4.8:
                advice += "✅ Your rating is excellent! Keep delivering quality work. 🎯\n"
            elif rating_float >= 4.5:
                advice += "⚡ Your rating is good, but aim for 4.8+ by improving response time and quality.\n"
            else:
                advice += "❗ Your rating is low. Try to provide better customer service and ask for positive reviews.\n"

        if orders != "N/A":
            orders_int = int(orders)
            if orders_int >= 50:
                advice += "🔥 You have many completed orders! Consider raising your prices.\n"
            elif orders_int >= 10:
                advice += "📈 You're getting good orders! Try optimizing your gig for better visibility.\n"
            else:
                advice += "💡 You need more sales! Share your gig on social media and offer promotions.\n"

        await update.message.reply_text(
            f"📊 Fiverr Profile Analysis for {fiverr_username}:\n"
            f"- ⭐ Rating: {rating}\n"
            f"- ✅ Completed Orders: {orders}\n"
            f"- 🎨 Top Gig: {gig_title}\n"
            f"- 🔗 [View Profile]({profile_url})\n\n"
            f"{advice}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("❌ Error fetching Fiverr profile. Make sure the username is correct.")

### **2️⃣ Add Handlers & Start Bot**
def main():
    """Start the bot and add all command handlers."""
    app.add_handler(CommandHandler("analyze", analyze))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
