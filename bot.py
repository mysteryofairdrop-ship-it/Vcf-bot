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
        "• Name: Raj, Phone: 9876543210\n"
        "• Raj - 9876543210\n"
        "• Raj 9876543210\n"
        "• Raj\\n9876543210\\nraj@email.com\n"
        "• मेरा नाम राज है, मेरा नंबर ९८७६५४३२१० है\n"
        "• Raj, 9876543210, raj@email.com\n\n"
        "📍 **Mujhe samajhne ki aadat hai!**\n"
        "Kisi bhi format mein bhejiye, main banajaunga VCF file!"
    )
    await update.message.reply_text(help_text)

# Smart data extraction function
def extract_contact_info(text):
    # Convert Hindi numbers to English
    text = convert_hindi_numbers(text)
    
    # Initialize data
    data = {'name': 'Unknown', 'phone': '', 'email': '', 'org': ''}
    
    # Common patterns
    patterns = [
        # Pattern 1: Name: value, Phone: value
        r'(?:name|nama|naam|नाम|نام)[\s:]*([^\n,]+)[,\n]*(?:phone|number|mobile|फोन|नंबर|موبایل)[\s:]*([+\d\s-]+)',
        # Pattern 2: Phone: value, Name: value  
        r'(?:phone|number|mobile|फोन|नंबर|موبایل)[\s:]*([+\d\s-]+)[,\n]*(?:name|nama|naam|नाम|نام)[\s:]*([^\n,]+)',
        # Pattern 3: Name - Phone
        r'([^\d+\n,]+?)[\s-]+([+\d][\d\s-]{8,})',
        # Pattern 4: Phone - Name
        r'([+\d][\d\s-]{8,})[\s-]+([^\d+\n,]+)',
        # Pattern 5: Just phone number (extract from text)
        r'([+\d][\d\s-]{8,})',
        # Pattern 6: Email pattern
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if 'name' in pattern and 'phone' in pattern:
                data['name'] = matches[0][0].strip()
                data['phone'] = matches[0][1].strip()
            elif 'phone' in pattern and 'name' in pattern:
                data['phone'] = matches[0][0].strip()
                data['name'] = matches[0][1].strip()
            elif pattern == patterns[2]:  # Name - Phone
                data['name'] = matches[0][0].strip()
                data['phone'] = matches[0][1].strip()
            elif pattern == patterns[3]:  # Phone - Name
                data['phone'] = matches[0][0].strip()
                data['name'] = matches[0][1].strip()
            elif pattern == patterns[4]:  # Just phone
                data['phone'] = matches[0].strip()
                # Try to extract name from remaining text
                name_match = re.search(r'([^\d+\n,]+)', text.replace(data['phone'], ''))
                if name_match:
                    data['name'] = name_match.group(1).strip()
            elif pattern == patterns[5]:  # Email
                data['email'] = matches[0].strip()
    
    # Clean up the data
    data['name'] = data['name'].title()
    data['phone'] = re.sub(r'\s+', '', data['phone'])  # Remove spaces from phone
    
    # If no name found, use first word from text
    if data['name'] == 'Unknown':
        words = text.split()
        if words:
            data['name'] = words[0].title()
    
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

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Extract information using smart parser
    data = extract_contact_info(user_text)
    
    # If no phone found, ask for it
    if not data['phone']:
        await update.message.reply_text(
            "❌ Mujhe phone number nahi mila.\n\n"
            "Kripya phone number bhejiye:\n"
            "Example: 9876543210 ya +919876543210"
        )
        return
    
    # Generate VCF
    vcf_data = generate_vcf(data['name'], data['phone'], data['email'])
    
    # Create filename
    filename = f"{data['name'].replace(' ', '_')}.vcf"
    
    # Save and send file
    with open(filename, 'w') as f:
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
    await update.message.reply_text("❌ Kuch error aaya hai. Thodi der baad try karein.")

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    application.run_polling()
    print("Bot started successfully!")

if __name__ == '__main__':
    main()