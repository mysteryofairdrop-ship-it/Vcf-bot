import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Bot Token - YAHI DALNA HAI
BOT_TOKEN = "8150871986:AAFuCQYErxA2ov9OaNdsL2_P6m5Zy_P7OJs"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **VCF Bot Ready!**\n\n"
        "Mujhe kisi ka naam aur phone number bhejo:\n\n"
        "**Jaise:**\n"
        "• `Raj 9876543210`\n"
        "• `Priya - 9123456789`\n"
        "• `Name: Amit, Phone: 9812345678`\n"
        "• `Sonia 9988776655 sonia@example.com`"
    )

# Number nikalne ka function
def find_phone_number(text):
    patterns = [
        r'(\+91[6-9]\d{9})', 
        r'([6-9]\d{9})',
        r'(\d{5}[\s-]?\d{5})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Spaces aur dashes hatao
            clean_number = re.sub(r'[\s-]', '', match.group(1))
            return clean_number
    return None

# Name nikalne ka function
def find_name(text, phone_number):
    # Pehle number ko text se hatao
    text_without_number = text.replace(phone_number, '')
    
    # Email hatao (agar hai toh)
    text_without_number = re.sub(r'\S+@\S+', '', text_without_number)
    
    # Special characters hatao
    clean_text = re.sub(r'[^a-zA-Zअ-ज़\s]', ' ', text_without_number)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Pehla 2-3 shabd naam hai
    words = clean_text.split()
    if words:
        return ' '.join(words[:3]).title()
    else:
        return "Contact"

# VCF banane ka function
def make_vcf(name, phone):
    return f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD"""

# Message handle karna
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Phone number dhundho
    phone = find_phone_number(user_text)
    if not phone:
        await update.message.reply_text("❌ Mujhe phone number nahi mila. Kripya number sahi se likhein.")
        return
    
    # Name dhundho
    name = find_name(user_text, phone)
    
    # VCF banayo
    vcf_data = make_vcf(name, phone)
    filename = f"{name.replace(' ', '_')}.vcf"
    
    # File banao aur bhejo
    with open(filename, 'w') as f:
        f.write(vcf_data)
    
    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=f,
            caption=f"✅ **VCF File Ready!**\n\n👤 {name}\n📞 {phone}"
        )
    
    # File delete karo
    os.remove(filename)

# Main function
def main():
    # Bot start karo
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands add karo
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Bot chalao
    print("Bot shuru ho raha hai...")
    app.run_polling()
    print("Bot band ho gaya")

if __name__ == '__main__':
    main()