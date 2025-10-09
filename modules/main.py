import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Document
from vars import API_ID, API_HASH, BOT_TOKEN
from globals import quality, thumb, CR  # Assuming globals has these

app = Client("video_pdf_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Resolution formats for yt-dlp
RESOLUTIONS = {
    '144': 'worst[height<=144]',
    '240': 'best[height<=240]',
    '360': 'best[height<=360]',
    '480': 'best[height<=480]',
    '720': 'best[height<=720]',
    '1080': 'best[height<=1080]'
}

# Default quality
if not hasattr(globals, 'quality') or globals.quality not in RESOLUTIONS:
    globals.quality = '720'  # Default to 720p

def download_with_yt_dlp(url, res_quality):
    """Download video or PDF using yt-dlp"""
    ydl_opts = {
        'format': RESOLUTIONS.get(res_quality, 'best[height<=720]'),
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            ext = info.get('ext', 'mp4')
            file_path = f"{title}.{ext}"
            
            # Check if it's a PDF
            if ext.lower() == 'pdf':
                return file_path, 'document'
            
            # For video
            return file_path, 'video'
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

# Handler for text messages (plain URLs)
@app.on_message(filters.text & filters.private)
async def handle_url_text(client: Client, message: Message):
    url = message.text.strip()
    if not ('http' in url or 'www' in url):
        await message.reply("❌ Please send a valid URL or TXT file with URL!")
        return
    
    await process_download(client, message, url)

# Handler for document (TXT file)
@app.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    if not message.document.file_name.endswith('.txt'):
        await message.reply("❌ Please send a .txt file!")
        return
    
    await message.reply("⏳ Processing TXT file...")
    
    # Download the TXT file
    file_path = await message.download()
    try:
        # Read the URL from the TXT file
        with open(file_path, 'r', encoding='utf-8') as f:
            url = f.read().strip()
            if not ('http' in url or 'www' in url):
                await message.reply("❌ No valid URL found in the TXT file!")
                return
        
        await process_download(client, message, url)
    except Exception as e:
        await message.reply(f"❌ Error reading TXT file: {str(e)}")
    finally:
        os.remove(file_path)  # Clean up the downloaded TXT file

async def process_download(client: Client, message: Message, url):
    await message.reply("⏳ Downloading... Please wait.")
    
    try:
        file_path, file_type = download_with_yt_dlp(url, globals.quality)
        
        caption = f"✅ Downloaded by {CR}\nTitle: {os.path.splitext(os.path.basename(file_path))[0]} [{globals.quality}p]"
        
        if file_type == 'document':
            await message.reply_document(
                document=file_path,
                caption=caption,
                thumb=thumb if thumb != '/d' else None
            )
        else:
            await message.reply_video(
                video=file_path,
                caption=caption,
                thumb=thumb if thumb != '/d' else None
            )
        
        # Clean up
        os.remove(file_path)
        
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# Settings for quality (similar to your previous code)
@app.on_callback_query(filters.regex("quality_command"))
async def set_quality(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("144p", callback_data="q_144"), InlineKeyboardButton("240p", callback_data="q_240")],
        [InlineKeyboardButton("360p", callback_data="q_360"), InlineKeyboardButton("480p", callback_data="q_480")],
        [InlineKeyboardButton("720p", callback_data="q_720"), InlineKeyboardButton("1080p", callback_data="q_1080")],
        [InlineKeyboardButton("All", callback_data="q_all")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])
    await callback_query.message.edit_text("Select Quality:", reply_markup=keyboard)

for res in ['144', '240', '360', '480', '720', '1080']:
    @app.on_callback_query(filters.regex(f"q_{res}"))
    async def set_res(client, callback_query):
        globals.quality = res
        await callback_query.answer(f"Quality set to {res}p")

@app.on_callback_query(filters.regex("q_all"))
async def set_all(client, callback_query):
    globals.quality = 'best'  # For all, but you can modify to download multiple
    await callback_query.answer("All qualities enabled (modify code for multi-download)")

if __name__ == "__main__":
    app.run()
