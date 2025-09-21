import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Apna Bot Token yahaan daalein
BOT_TOKEN = "8150871986:AAFuCQYErxA2ov9OaNdsL2_P6m5Zy_P7OJs"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! 👋 Main VCF Bot hoon.\n"
        "Mujhe kisi ka naam, phone number, email, aur anya details bhejiye, main aapko VCF file bana kar dunga.\n\n"
        "Example:\n"
        "Name: Raj Sharma\n"
        "Phone: +919876543210\n"
        "Email: raj@example.com"
    )

# VCF generate karne wala function
def generate_vcf(name, phone, email=None, org=None):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL;TYPE=CELL:{phone}
"""
    if email:
        vcf_content += f"EMAIL:{email}\n"
    if org:
        vcf_content += f"ORG:{org}\n"
    vcf_content += "END:VCARD"
    return vcf_content

# Message handle karein
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    lines = user_text.split('\n')
    data = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip().lower()] = value.strip()
    
    name = data.get('name', 'Unknown')
    phone = data.get('phone', '')
    email = data.get('email', '')
    org = data.get('org', '')
    
    if not phone:
        await update.message.reply_text("Phone number diye bina VCF nahi bana sakta. Kripya phone number provide karein.")
        return
    
    vcf_data = generate_vcf(name, phone, email, org)
    
    # VCF file save karein temporarily
    filename = f"{name.replace(' ', '_')}.vcf"
    with open(filename, 'w') as f:
        f.write(vcf_data)
    
    # File send karein
    with open(filename, 'rb') as f:
        await update.message.reply_document(document=f, caption="Yeh lo aapki VCF file! 📇")
    
    # Temporary file delete karein
    os.remove(filename)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()