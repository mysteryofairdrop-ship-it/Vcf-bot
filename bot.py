import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Bot Token - YAHAN APNA TOKEN DALDO
BOT_TOKEN = "8150871986:AAFuCQYErxA2ov9OaNdsL2_P6m5Zy_P7OJs"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Smart VCF Bot**\n\n"
        "Mujhe kisi bhi format mein details bhejiye:\n\n"
        "**Examples:**\n"
        "• `Raj 9876543210`\n"
        "• `Name: Raj, Phone: 9876543210`\n"
        "• `मेरा नाम राज है नंबर ९८७६५४३२१०`\n"
        "• `Raj - 9876543210`\n"
        "• `+919876543210 Raj`\n\n"
        "📍 **Mujhe samajhne ki aadat hai!**"
    )
    await update.message.reply_text(help_text)

# Smart data extraction function - YE WALA USE KARO
def extract_contact_info(text):
    # Convert Hindi numbers to English
    text = convert_hindi_numbers(text)
    
    # Initialize data
    data = {'name': 'Contact', 'phone': '', 'email': ''}
    
    # 1. PEHLE PHONE NUMBER DHUNDHO (Sabse Important)
    phone_patterns = [
        r'(\+?91[-\s]?[6-9]\d{9})',  # +91 9876543210
        r'(\+?1[-\s]?[2-9]\d{2}[-\s]?\d{3}[-\s]?\d{4})',  # US Numbers
        r'([6-9]\d{9})',  # 9876543210
        r'([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{4})',  # 987-654-3210
    ]
    
    found_phone = None
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            found_phone = match.group(1)
            # Phone number ko text se remove kar do taki name na mile
            text = text.replace(found_phone, '', 1)
            break
    
    if not found_phone:
        return None  # Phone nahi mila toh kuch nahi hoga
    
    data['phone'] = re.sub(r'[\s-]', '', found_phone)  # Clean phone number
    
    # 2. AB NAME DHUNDHO (Phone ke alawa jo bache)
    # Text ko saaf karo
    clean_text = re.sub(r'[^a-zA-Zअ-ज़\s]', ' ', text)  # Sirf letters aur spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Extra spaces hatayo
    
    if clean_text and len(clean_text) > 1:
        # Words mein split karo aur first 2-3 words ko name maano
        words = clean_text.split()
        if len(words) > 3:
            data['name'] = ' '.join(words[:3]).title()
        else:
            data['name'] = clean_text.title()
    else:
        # Agar name nahi mila toh phone ke last 4 digits use karo
        data['name'] = f"Contact_{data['phone'][-4:]}"
    
    # 3. EMAIL DHUNDHO (Optional)
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        data['email'] = email_match.group(1)
    
    return data

# Convert Hindi numbers to English
def convert_hindi_numbers(text):
    hindi_to_english = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    for hindi, english in hindi_to_english.items():
        text = text.replace(hindi, english)
    return text

# VCF generate function
def generate_vcf(name, phone, email=None):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL;TYPE=CELL,VOICE:{phone}
"""
    if email:
        vcf_content += f"EMAIL;TYPE=INTERNET,HOME:{email}\n"
    vcf_content += "END:VCARD"
    return vcf_content

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Extract information using smart parser
    data = extract_contact_info(user_text)
    
    if not data:
        await update.message.reply_text(
            "❌ Mujhe koi phone number nahi mila.\n\n"
            "Kripya message mein phone number bhejiye:\n"
            "Example: `Raj 9876543210` ya `+919876543210`"
        )
        return
    
    # Generate VCF
    vcf_data = generate_vcf(data['name'], data['phone'], data['email'])
    
    # Create filename
    filename = f"{data['name'].replace(' ', '_')}.vcf"
    
    # Save and send file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(vcf_data)
    
    with open(filename, 'rb') as f:
        caption = (
            f"✅ **VCF File Ready!**\n\n"
            f"👤 Name: {data['name']}\n"
            f"📞 Phone: {data['phone']}\n"
            f"📧 Email: {data['email'] or 'Not provided'}\n\n"
            f"💾 Save to contacts and share!"
        )
        await update.message.reply_document(
            document=f,
            caption=caption,
            parse_mode='Markdown'
        )
    
    # Clean up
    os.remove(filename)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)
    try:
        await update.message.reply_text("❌ Kuch error aaya hai. Thodi der baad try karein.")
    except:
        pass

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("Bot starting...")
    application.run_polling()
    print("Bot started successfully!")

if __name__ == '__main__':
    main()