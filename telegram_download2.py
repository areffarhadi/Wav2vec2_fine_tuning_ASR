from telethon import TelegramClient
import asyncio
import os
import sqlite3
import time

# Your account details
api_id = 27026494
api_hash = 'b0feccae071ddb5714042204f1eee290'
phone_number = '+41762295575'
download_folder = 'telegram_videos'
source_channel = '@kafiha'

# Maximum download size in bytes (100 MB)
MAX_DOWNLOAD_SIZE = 100 * 1024 * 1024

# Function to clean up locked session
def cleanup_session():
    try:
        if os.path.exists('session.session'):
            os.remove('session.session')
        if os.path.exists('session.session-journal'):
            os.remove('session.session-journal')
    except Exception as e:
        print(f"Error cleaning up session: {e}")

# Function to create client with retry
def create_client(max_retries=3):
    for attempt in range(max_retries):
        try:
            cleanup_session()
            return TelegramClient('session', api_id, api_hash)
        except sqlite3.OperationalError:
            if attempt < max_retries - 1:
                print(f"Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                raise
        except Exception as e:
            print(f"Error creating client: {e}")
            raise

# Create client
client = create_client()

async def download_videos():
    try:
        await client.start(phone=phone_number)
        print("Client Created")
        
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        channel = await client.get_entity(source_channel)
        
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
        video_mime_types = ('video/', 'application/x-mpegURL')
        
        download_count = 0
        
        async for message in client.iter_messages(channel):
            if message.file:
                is_video = False
                if message.file.mime_type:
                    is_video = any(message.file.mime_type.startswith(mime) for mime in video_mime_types)
                
                file_name = message.file.name or f"video_{message.id}"
                if file_name:
                    _, ext = os.path.splitext(file_name)
                    is_video = is_video or ext.lower() in video_extensions
                
                if is_video:
                    if not file_name:
                        file_name = f"video_{message.id}.mp4"
                    elif not any(file_name.lower().endswith(ext) for ext in video_extensions):
                        file_name += '.mp4'
                    
                    full_path = os.path.join(download_folder, file_name)
                    
                    if not os.path.exists(full_path):
                        print(f"Downloading: {file_name}")
                        try:
                            if message.file.size > MAX_DOWNLOAD_SIZE:
                                print(f"File size is over 100MB, downloading only the first 100MB of {file_name}")
                                await client.download_media(
                                    message, file=full_path, thumb=None, limit=MAX_DOWNLOAD_SIZE
                                )
                            else:
                                await client.download_media(message, full_path)
                            download_count += 1
                            print(f"Successfully downloaded: {file_name}")
                        except Exception as e:
                            print(f"Error downloading {file_name}: {str(e)}")
                    else:
                        print(f"File already exists, skipping: {file_name}")
            else:
                print("Message has no file attached. Skipping...")
        
        print(f"Download completed! Total videos downloaded: {download_count}")
    
    except Exception as e:
        print(f"Error in download_videos: {e}")
    finally:
        await client.disconnect()

async def main():
    try:
        await download_videos()
    finally:
        if client.is_connected():
            await client.disconnect()
        cleanup_session()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup_session()
        try:
            loop.close()
        except:
            pass

