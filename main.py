YOUR_BOT_TOKEN= '5624529763:AAFlo1zSa5pve-YjUj1qBtV2pDZo30R5pWk'
import telebot
from bs4 import BeautifulSoup
import requests
import asyncio
import edge_tts
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import textwrap

from pathlib import Path
Path("generated").mkdir(parents=True, exist_ok=True)

# Set up the Telegram bot
bot = telebot.TeleBot(YOUR_BOT_TOKEN)

VOICE = "bn-BD-NabanitaNeural"
MP3_OUTPUT_PATH = "generated/audio.mp3"
MP4_OUTPUT_PATH = "generated/video.mp4"
SOURCE_IMAGE_PATH = "generated/source-image.jpg"
RESIZED_IMAGE_PATH = "generated/resized-image.jpg"  # resized image accourding to the weidth of video
BACKGROUND_IMAGE_PATH = "preset/background.jpg"
FINAL_IMAGE_PATH = "generated/final-image-with-text.jpg"  # final image that will be the video image

async def _generateMp3(text) -> None:
    communicate = edge_tts.Communicate(text, VOICE,rate='+7%')
    await communicate.save(MP3_OUTPUT_PATH)



def get_image_width(image):
    with Image.open(image) as img:
        return img.width

def resize_image_with_fixed_width(image, width):
    with Image.open(image) as img:
        aspect_ratio = img.width / img.height
        height = round(width / aspect_ratio)
        img = img.resize((width, height))
        return img


def generateVideoFile(title):
    
    img = resize_image_with_fixed_width(SOURCE_IMAGE_PATH, get_image_width(BACKGROUND_IMAGE_PATH))
    img.save(RESIZED_IMAGE_PATH)
    
    resizedImage = Image.open(RESIZED_IMAGE_PATH)
    
    resizedImageWidth, resizedImageHeight = resizedImage.size
    
    #code from ChatGPT 
    new_height = int(resizedImageWidth * 16 / 9)
    padding = (new_height - resizedImageHeight) // 2
    #end code from ChatGPT 
    
    
    
    
    final_image =Image.open(BACKGROUND_IMAGE_PATH)
    final_image.paste(resizedImage, (0, padding))
    
    
    draw = ImageDraw.Draw(final_image)
    font = ImageFont.truetype("preset/font.ttf", 50, encoding="utf-8")
    text_width, text_height = draw.textsize(title, font=font)
    
    margin = 40
    offset =  resizedImageHeight + padding +(text_height*1)
    for line in textwrap.wrap(title, width=30):
        draw.text((margin, offset),line , font=font, fill='#fff',stroke_width=2, stroke_fill="red")
        offset += font.getsize(line)[1]
    
    final_image.save(FINAL_IMAGE_PATH)
    
    audio = mp.AudioFileClip(MP3_OUTPUT_PATH)
    image = mp.ImageClip(FINAL_IMAGE_PATH)
    video = image.set_audio(audio).set_duration(audio.duration)
    video.write_videofile(MP4_OUTPUT_PATH, fps=24)

def getDataFromUrl(url,replyMessage):
    response = requests.get(url)
    soup = BeautifulSoup(response.text,features="lxml")
    bot.edit_message_text("Got data from url. processing...", replyMessage.chat.id,replyMessage.id)
    
    metaDescriptionTag =  soup.find("meta", property="og:description")
    metaImageTag =  soup.find("meta", attrs={"name":"image"})
    metaTitleTag =  soup.find("meta", attrs={"name":"title"})
    
    title =metaTitleTag["content"] if metaTitleTag else "কোনো শিরোনাম পাওয়া যায়নি"
    descriptionHtml =metaDescriptionTag["content"] if metaDescriptionTag else "কোনো খবর পাওয়া যায়নি"
    image =metaImageTag["content"] if metaImageTag else "https://static.vecteezy.com/system/resources/previews/005/337/799/original/icon-image-not-found-free-vector.jpg"
    contentSoup = BeautifulSoup(descriptionHtml,features="lxml")
    for strong in contentSoup.find_all('strong'):
        strong.decompose()
        for aTag in strong.find_next_siblings():
            aTag.decompose()

    description =contentSoup.text
    img_data = requests.get(image).content
    with open(SOURCE_IMAGE_PATH, 'wb') as handler:
        handler.write(img_data)
        
    bot.edit_message_text("Data processed. generating mp3...", replyMessage.chat.id,replyMessage.id)
    asyncio.run(_generateMp3(title+"। "+description))
    bot.edit_message_text("mp3 generated! generating video with the mp3...", replyMessage.chat.id,replyMessage.id)
    generateVideoFile(title)
   



# Function to handle incoming messages
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Hi! Send me a news URL from somoynews.tv website and i will make you a video')

@bot.message_handler(func=lambda message: True)
def reply(message):
    replyMessage = bot.reply_to(message, "Requesting data from the url")
    try:
        
        getDataFromUrl(message.text,replyMessage)
        bot.edit_message_text("Video Generated. sending video to you", replyMessage.chat.id,replyMessage.id)
        document = open(MP4_OUTPUT_PATH, 'rb')
        bot.send_document(document=document,reply_to_message_id=message.id,chat_id=message.chat.id)
        bot.edit_message_text("Everything Complite", replyMessage.chat.id,replyMessage.id)

    except Exception as e:
        bot.edit_message_text(e, replyMessage.chat.id,replyMessage.id)
   

# Start the bot
bot.polling()

