import os
import logging
import re
import tempfile
import zipfile
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Bot Token
BOT_TOKEN = "8150871986:AAFuCQYErxA2ov9OaNdsL2_P6m5Zy_P7OJs"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Bulk VCF Generator Bot**\n\n"
        "📦 **50+ Contacts ke liye Ready!**\n\n"
        "Mujhe contacts list bhejiye:\n\n"
        "**Format 1 (Single):**\n"
        "Raj, 9876543210, raj@email.com\n\n"
        "**Format 2 (Multiple):**\n"
        "Raj, 9876543210\n"
        "Priya, 9123456789\n"
        "Amit, 9812345678\n\n"
        "**Format 3 (Bulk):**\n"
        "Name, Phone, Email\n"
        "Raj, 9876543210, raj@email.com\n"
        "Priya, 9123456789, priya@email.com\n"
        "Amit, 9812345678, amit@email.com\n\n"
        "📍 **Main 1000+ contacts bana sakta hoon!**"
    )
    await update.message.reply_text(help_text)

# Extract single contact info
def extract_single_contact(text):
    # Clean the text
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Different patterns for extraction
    patterns = [
        # Name, Phone, Email
        r'([^,]+),([^,]+),([^,]+)',
        # Name, Phone
        r'([^,]+),([^,]+)',
        # Name - Phone - Email
        r'([^-]+)-([^-]+)-([^-]+)',
        # Name - Phone
        r'([^-]+)-([^-]+)',
        # Just phone number
        r'(\+?[0-9\s\-\(\)]{8,})'
    ]
    
    contact = {'name': 'Unknown', 'phone': '', 'email': ''}
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = [g.strip() for g in match.groups()]
            
            if len(groups) >= 2:
                contact['name'] = groups[0]
                contact['phone'] = re.sub(r'\D', '', groups[1])  # Keep only digits
                
                if len(groups) >= 3:
                    contact['email'] = groups[2]
            
            elif len(groups) == 1 and pattern == patterns[4]:
                contact['phone'] = re.sub(r'\D', '', groups[0])
                # Try to extract name from remaining text
                name_part = text.replace(groups[0], '').strip()
                if name_part:
                    contact['name'] = name_part
            
            break
    
    # If phone is found but name is still Unknown, use "Contact"
    if contact['phone'] and contact['name'] == 'Unknown':
        contact['name'] = f"Contact_{contact['phone'][-4:]}"
    
    return contact

# Process bulk contacts
def process_bulk_contacts(text):
    contacts = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.lower().startswith(('name', 'phone', 'email')):
            contact = extract_single_contact(line)
            if contact['phone']:  # Only add if phone exists
                contacts.append(contact)
    
    return contacts

# Generate VCF content
def generate_vcf(name, phone, email=None):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL;TYPE=CELL:{phone}
"""
    if email and '@' in email:
        vcf_content += f"EMAIL:{email}\n"
    vcf_content += "END:VCARD"
    return vcf_content

# Create ZIP file with multiple VCFs
def create_contacts_zip(contacts):
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "contacts.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i, contact in enumerate(contacts, 1):
                vcf_content = generate_vcf(contact['name'], contact['phone'], contact['email'])
                vcf_filename = f"{contact['name'].replace(' ', '_')}_{i}.vcf"
                vcf_path = os.path.join(temp_dir, vcf_filename)
                
                with open(vcf_path, 'w', encoding='utf-8') as vcf_file:
                    vcf_file.write(vcf_content)
                
                zipf.write(vcf_path, vcf_filename)
        
        return zip_path

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text
        
        # Process contacts
        contacts = process_bulk_contacts(user_text)
        
        if not contacts:
            await update.message.reply_text(
                "❌ Mujhe koi valid contacts nahi mile.\n\n"
                "Kripya is format mein bhejiye:\n"
                "Raj, 9876543210\n"
                "Priya, 9123456789\n"
                "Amit, 9812345678"
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            f"🔄 Processing {len(contacts)} contacts..."
        )
        
        # Create ZIP file
        zip_path = create_contacts_zip(contacts)
        
        # Send ZIP file
        with open(zip_path, 'rb') as zip_file:
            await update.message.reply_document(
                document=zip_file,
                filename="contacts.zip",
                caption=f"✅ **{len(contacts)} Contacts Ready!**\n\n"
                       f"📦 ZIP file download karein aur extract karein\n"
                       f"📞 Phir contacts mein save karein\n\n"
                       f"✨ Total Contacts: {len(contacts)}",
                parse_mode='Markdown'
            )
        
        # Delete processing message
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=processing_msg.message_id
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Kuch error aaya hai. Thodi der baad try karein.\n"
            "Please check your input format."
        )

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)
    await update.message.reply_text("❌ Server error. Please try again later.")

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
    print("✅ Bulk VCF Bot started successfully!")

if __name__ == '__main__':
    main()