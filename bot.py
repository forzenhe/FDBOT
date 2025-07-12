import asyncio
import logging
import re
import random
welcome_messages = [
    "Hey cutie 😘 Ready for something spicy?",
    "You again? 😏 Couldnt resist, huh?",
    "Welcome back, troublemaker 😈",
    "Missed me, sugar? 😋",
    "Dont just /start me… impress me 😎💋",
    "Your favorite bot is back, and naughty as ever 💋🔥",
    "Starting me is easy… handling me? Thats the challenge 😈😉"
     "Well, well, well... look who just slid into my DMs. 😏💋",
    "I only respond to deep links and deep feelings. Got either? 😘🔗",
    "You /start-ed me... now finish what you came for. 💦😈",
    "I'm like a secret folder — full of things you *probably* shouldn't open. 🔐🍑",
    "You press buttons, I deliver pleasure... in file format. 💌📁",
    "Careful, darling — I dont just send files, I send *feelings*. 💘💻",
    "One click and am yours... until timeout. ⏳❤️‍🔥",
    "You had me at /start. 🥺💞",
    "Files? Oh baby, I thought you were here for me. 😍📦",
    "If flirting was a file type, Id be in .zip — tightly packed with love. 😏💾",
    "Youve just unlocked level 1 of *bot seduction*. Ready to play? 🎮💋",
    "Im not clingy, but if you leave me unread... I might cry in binary. 🥹🧬",
    "Talk data to me, baby. 🧠🔞",
    "I serve files with a side of sass and a sprinkle of seduction. 🍽️💃",
    "Ugh... another user trying to open me up. Typical. 😒😈",
    "My love is like this bot — always online for you. 💞🤖",
    "You came here for files, but I might just steal your heart. 🫶📲",
    "My files arent the only thing thats hot. 🔥📁😉",
    "Dont just /start me. Tease me. Tempt me. Make it worth my bandwidth. 💋🔌",
    "Your presence has been detected. Mood: Flirty. Protocol: Activated. 🥵💿"
    
]

import uuid
import json
import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, CHANNEL_ID, LOG_GROUP_ID, SHRINKME_API_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# File to store mappings persistently
STORAGE_FILE = "file_mappings.json"

def load_file_mappings():
    """Load file mappings from JSON file"""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_file_mappings(mappings):
    """Save file mappings to JSON file"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(mappings, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving mappings: {e}")



        

# Load existing mappings on startup
file_mappings = load_file_mappings()
print(f"📋 Loaded {len(file_mappings)} existing file mappings")



def generate_unique_id():
    return str(uuid.uuid4())[:8]

def shorten_url(url: str) -> str:
    """Shorten a URL using Shrinkme.io API"""
    try:
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API_TOKEN}&url={url}"
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200 and response.json().get("status") == "success":
            shortened_url = response.json().get("shortenedUrl")
            print(f"✅ Shortened URL: {shortened_url}")
            return shortened_url
        else:
            print(f"⚠️ Failed to shorten URL: {response.text}")
            return url
    except Exception as e:
        print(f"❌ Error shortening URL: {e}")
        return url

async def handle_new_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if update.effective_chat.id != CHANNEL_ID:
        return

    file_id = None
    media_type = None
    
    if message.video:
        file_id = message.video.file_id
        media_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        media_type = "document"

    if file_id:
        unique_id = generate_unique_id()
        
        # Store in both memory and file
        file_mappings[unique_id] = {
            'file_id': file_id,
            'media_type': media_type,
            'message_id': message.message_id,
            'channel_id': CHANNEL_ID
        }
        
        # Save to file immediately
        save_file_mappings(file_mappings)
        
        log_entry = f"ID:{unique_id}\nFILE_ID:{file_id}\nTYPE:{media_type}\nMSG_ID:{message.message_id}\nCHANNEL_ID:{CHANNEL_ID}"
        print(f"✅ New media detected. Saving to log group:\n{log_entry}")
        
        # Forward media with log entry to log group
        try:
            if media_type == "video":
                log_message = await context.bot.send_video(
                    chat_id=LOG_GROUP_ID,
                    video=file_id,
                    caption=log_entry
                )
            elif media_type == "photo":
                log_message = await context.bot.send_photo(
                    chat_id=LOG_GROUP_ID,
                    photo=file_id,
                    caption=log_entry
                )
            else:  # document
                log_message = await context.bot.send_document(
                    chat_id=LOG_GROUP_ID,
                    document=file_id,
                    caption=log_entry
                )
            
            # Store the log message ID
            file_mappings[unique_id]['log_msg_id'] = log_message.message_id
            save_file_mappings(file_mappings)
            print(f"✅ Media and log sent to log group for ID {unique_id}")
            
        except Exception as e:
            print(f"❌ Error forwarding media to log group: {e}")
            # Fallback: send only log entry
            log_message = await context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=log_entry
            )
            file_mappings[unique_id]['log_msg_id'] = log_message.message_id
            save_file_mappings(file_mappings)

        deep_link = f"https://t.me/{context.bot.username}?start={unique_id}"
        shortened_link = shorten_url(deep_link)
        print(f"🔗 Deep link generated: {deep_link}")
        print(f"🔗 Shortened link: {shortened_link}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Click Here", url=shortened_link)]])
        await message.reply_text(
            "Click the button to get this media",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    print(f"⚡️ /start command triggered with args: {args}")

    if not args:
        if welcome_messages:
            welcome = random.choice(welcome_messages)
            print(f"✅ Random welcome message selected: {welcome}")  # optional debug
        else:
            welcome = "Hey! I'm your sexy little media bot 😘"
            print("⚠️ No welcome messages loaded — using fallback.")
        await update.message.reply_text(welcome)
        return




    unique_id = args[0]
    
    # Check in file mappings (persistent storage)
    if unique_id in file_mappings:
        file_data = file_mappings[unique_id]
        file_id = file_data['file_id']
        media_type = file_data['media_type']
        message_id = file_data.get('message_id')
        channel_id = file_data.get('channel_id', CHANNEL_ID)
        
        print(f"✅ FILE_ID found in storage for ID {unique_id}: {file_id}, Type: {media_type}")
        
        # Try to get fresh media from channel using message ID
        try:
            if message_id:
                print(f"🔍 Fetching fresh media from channel {channel_id} using message_id: {message_id}")
                
                # Method 1: Try to copy the message
                try:
                    copied_msg = await context.bot.copy_message(
                        chat_id=update.effective_user.id,
                        from_chat_id=channel_id,
                        message_id=message_id,
                        caption="🗑️ Auto-deletes in 30min"
                    )
                    print(f"✅ Media copied successfully from channel for ID {unique_id}")
                    
                    # Schedule deletion after 30 minutes (only if job_queue is available)
                    if context.job_queue:
                        context.job_queue.run_once(
                            delete_media, 
                            1800,  # 30 minutes
                            data={'message_id': copied_msg.message_id, 'chat_id': update.effective_user.id, 'unique_id': unique_id}
                        )
                        print("✅ Auto-delete scheduled for 30 minutes")
                    else:
                        print("⚠️ Auto-delete not available (JobQueue not installed)")
                    return
                    
                except Exception as copy_error:
                    print(f"⚠️ Copy failed: {copy_error}. Trying direct send...")
                    
        except Exception as e:
            print(f"⚠️ Could not fetch fresh media from channel: {e}")
            
        # Fallback: Send using stored file_id
        await send_media_by_file_id(update, context, file_id, media_type, unique_id)
        
    else:
        # Try to search in log group as fallback
        print(f"🔍 Searching log group for ID: {unique_id}")
        result = await search_log_group(context, unique_id)
        
        if result:
            file_id, media_type, message_id = result
            print(f"✅ Found in log group for ID {unique_id}: {file_id}, Type: {media_type}")
            
            # Store in memory for future use
            file_mappings[unique_id] = {
                'file_id': file_id,
                'media_type': media_type,
                'message_id': message_id,
                'channel_id': CHANNEL_ID
            }
            save_file_mappings(file_mappings)
            
            await send_media_by_file_id(update, context, file_id, media_type, unique_id)
        else:
            print(f"❌ FILE_ID NOT FOUND for ID: {unique_id}")
            await update.message.reply_text("❌ Media not found or expired.")

async def send_media_by_file_id(update, context, file_id, media_type, unique_id):
    """Send media using file_id with proper error handling"""
    try:
        if media_type == "video":
            sent = await update.message.reply_video(
                video=file_id,
                caption="🗑️ Auto-deletes in 30min"
            )
        elif media_type == "photo":
            sent = await update.message.reply_photo(
                photo=file_id,
                caption="🗑️ Auto-deletes in 30min"
            )
        elif media_type == "document":
            sent = await update.message.reply_document(
                document=file_id,
                caption="🗑️ Auto-deletes in 30min"
            )
        else:
            # Fallback: try different types
            try:
                sent = await update.message.reply_video(
                    video=file_id,
                    caption="🗑️ Auto-deletes in 30min"
                )
            except:
                try:
                    sent = await update.message.reply_photo(
                        photo=file_id,
                        caption="🗑️ Auto-deletes in 30min"
                    )
                except:
                    sent = await update.message.reply_document(
                        document=file_id,
                        caption="🗑️ Auto-deletes in 30min"
                    )
        
        print(f"✅ Media sent successfully for ID {unique_id}")
        
        # Schedule deletion after 30 minutes (only if job_queue is available)
        if context.job_queue:
            context.job_queue.run_once(
                delete_media, 
                1800,  # 30 minutes
                data={'message_id': sent.message_id, 'chat_id': update.effective_user.id, 'unique_id': unique_id}
            )
            print("✅ Auto-delete scheduled for 30 minutes")
        else:
            print("⚠️ Auto-delete not available (JobQueue not installed)")
        
    except Exception as e:
        print(f"❌ Failed to send media: {e}")
        await update.message.reply_text("❌ Could not send media. File might be corrupted or too large.")

async def delete_media(context: ContextTypes.DEFAULT_TYPE):
    """Callback function to delete media after timeout"""
    data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=data['chat_id'],
            message_id=data['message_id']
        )
        print(f"🗑️ Media deleted after 30 minutes for ID {data['unique_id']}")
            
    except Exception as e:
        print(f"⚠️ Failed to delete media: {e}")

async def search_log_group(context: ContextTypes.DEFAULT_TYPE, unique_id: str):
    """
    Search log group for the unique_id
    This is a simplified approach - in production, use a database
    """
    try:
        # Try to get the latest few messages from log group
        # This is a workaround since direct message fetching is limited
        
        # Send a search query to log group and try to find recent messages
        search_msg = await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"🔍 Searching for ID: {unique_id}"
        )
        
        # Delete the search message
        await search_msg.delete()
        
        # Note: This is a limitation of the Bot API
        # For production, implement a proper database solution
        print("⚠️ Log group search is limited. Using file storage instead.")
        
        return None
        
    except Exception as e:
        print(f"❌ Error searching log group: {e}")
        return None

# Add cleanup command for old entries
async def cleanup_old_entries(context: ContextTypes.DEFAULT_TYPE):
    """Remove entries older than 7 days"""
    try:
        # This is a simple cleanup - in production, implement proper timestamp checking
        if len(file_mappings) > 1000:  # Keep only recent 1000 entries
            # Remove oldest entries (this is a simple approach)
            items = list(file_mappings.items())
            # Keep only the last 800 entries
            file_mappings.clear()
            file_mappings.update(dict(items[-800:]))
            save_file_mappings(file_mappings)
            print(f"🧹 Cleaned up old entries. Now have {len(file_mappings)} entries.")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    
    
    app = Application.builder().token(BOT_TOKEN).build()

    
    # Add handlers
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_new_media))
    app.add_handler(CommandHandler("start", start))
    
    # Schedule cleanup every 24 hours (only if job_queue is available)
    try:
        if app.job_queue:
            app.job_queue.run_repeating(cleanup_old_entries, interval=86400, first=86400)
            print("✅ Cleanup job scheduled")
        else:
            print("⚠️ JobQueue not available. Install with: pip install python-telegram-bot[job-queue]")
    except Exception as e:
        print(f"⚠️ Could not schedule cleanup job: {e}")
    
    print("🤖 Bot running...")
    print(f"📋 Current storage: {len(file_mappings)} file mappings")
    app.run_polling()

if __name__ == "__main__":
    main()