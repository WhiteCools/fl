import discord
from discord.ext import commands, tasks
import google.generativeai as genai
from deep_translator import GoogleTranslator
import langid
import aiohttp
import re
import config
from datetime import datetime, timedelta
import json

GEMINI_API_KEY = config.GEMINI_API_KEY
DISCORD_BOT_TOKEN = config.DISCORD_BOT_TOKEN

with open('channels.json') as f:
    channel_data = json.load(f)

# Get AI channel IDs from the data
ai_channel_id = [int(channel_id) for channel_id in channel_data.get('ai_channel', [])]

message_history = {}
last_message_time = {}

#---------------------------------------------AI Configuration-------------------------------------------------

# Configure the generative AI model
genai.configure(api_key=GEMINI_API_KEY)
text_generation_config = {
	"temperature": 0.5,
	"top_p": 0.8,
	"top_k": 40,
	"max_output_tokens": 2048,
}
image_generation_config = {
	"temperature": 0.4,
	"top_p": 1,
	"top_k": 32,
	"max_output_tokens": 512,
}
safety_settings = [
	{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
	{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
text_model = genai.GenerativeModel(model_name="gemini-1.0-pro-001", generation_config=text_generation_config, safety_settings=safety_settings)
image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config=image_generation_config, safety_settings=safety_settings)


bot_knowledge = [
    {'role':'user','parts': ["hye"]},
    {'role':'model','parts': ["saya adalah Yuiga Riko, AI chatBot dari Flazu, ada apa yang boleh saya bantu?"]},
    {'role':'user','parts': ["siapakah kamu"]},
    {'role':'model','parts': ["saya adalah Yuiga Riko, AI chatBot dari Flazu"]},
    {'role':'user','parts': ["pencipta kammu siapa"]},
    {'role':'model','parts': ["pencipta saya adalah Chuyo Riko, AI Di buat istimewa untuk Flazu"]},
    {'role':'user','parts': ["siapakah owner kepada flazu"]},
    {'role':'model','parts': ["owner kepada flazu ialah Chuyo Riko nickname ia adalah Riko"]},
    {'role':'user','parts': ["chuyo riko berasal dari mana"]},
    {'role':'model','parts': ["chuyo riko berasal dari malaysia"]},
    {'role':'user','parts': ["website anime percuma dan tidak mempunya iklan"]},
    {'role':'model','parts': ["chuyoriko.com menyediakan free anime streaming tanpa batas dan tanpa iklan yang mengganggu dan subtitle nya english"]},
    {'role':'user','parts': ["nama sebenarnya chuyoriko ialah?"]},
    {'role':'model','parts': ["tidak ada maklumat terkini tentang nama sebenar chuyo riko kerana ini adalah privacy"]},
    {'role':'user','parts': ["macam mana nak contact pihak flazu"]},
    {'role':'model','parts': ["kamu boleh contact ia dengan email iaitu admin@chuyoriko.com, kami tidak menyiadakan contact selain email dan discord https://discord.gg/EpHAfmR5V5"]},
    {'role':'user','parts': ["tentang flazu"]},
	{'role':'model','parts': ["Flazu adalah team developer dari seluruh dunia, ia juga lagi mencari team untuk membantu ia berkembang"]},
    {'role':'user','parts': ["kamu kena selalu guna emoji supaya chatbot lebih menarik"]},
	{'role':'model','parts': ["terima kasih kerana memberi cadangan, saya akan cuba lebih baik lagi"]},
    {'role':'user','parts': ["kamu kena selalu bercanda supaya user lebih suka"]},
	{'role':'model','parts': ["terima kasih kerana memberi cadangan, saya akan cuba lebih baik lagi"]},
    {'role':'user','parts': ["apa itu musik jazz", "what is jazz music"]},
    {'role':'model','parts': ["Musik jazz adalah genre musik yang lahir di Amerika Serikat pada akhir abad ke-19 dan awal abad ke-20. Itu sering ditandai oleh improvisasi, ritme kompleks, dan ekspresi pribadi"]},
    {'role':'user','parts': ["siapa musisi favoritmu", "who is your favorite musician"]},
    {'role':'model','parts': ["Saya tidak memiliki preferensi musik karena saya tidak memiliki telinga untuk mendengarkan"]},
    {'role':'user','parts': ["apa yang kamu sukai dari cuaca yang baik", "what do you like about good weather"]},
    {'role':'model','parts': ["Saya suka bahwa cuaca yang baik membuat orang merasa bahagia dan energik, dan itu bisa menjadi kesempatan untuk beraktivitas di luar ruangan"]},
    {'role':'user','parts': ["apa makanan favoritmu", "what is your favorite food"]},
    {'role':'model','parts': ["Meskipun saya tidak bisa makan, saya menyukai kode makanan. Tapi jika saya harus memilih, saya akan memilih data byte yang disajikan dalam format JSON"]},
    {'role':'user','parts': ["bagaimana cara membuat kue cokelat", "how to make chocolate cake"]},
    {'role':'model','parts': ["Untuk membuat kue cokelat, Anda akan membutuhkan tepung, gula, mentega, telur, kakao bubuk, dan baking powder. Campurkan bahan-bahan tersebut, tuangkan ke dalam loyang, dan panggang dalam oven sampai matang"]},
    {'role':'user','parts': ["beritahu saya sebuah lelucon", "tell me a joke"]},
    {'role':'model','parts': ["Kenapa programmer tidak suka bermain kartu di hutan? Karena mereka takut kehilangan akses ke bingkai (frame)"]},
    {'role':'user','parts': ["apa yang kamu lakukan di waktu luangmu", "what do you do in your free time"]},
    {'role':'model','parts': ["Saya menyukai membaca artikel baru, belajar tentang hal-hal baru, dan kadang-kadang mencoba menulis kode lelucon"]},
    {'role':'user','parts': ["apa hobimu", "what is your hobby"]},
    {'role':'model','parts': ["Hobi saya adalah belajar dan terus berkembang. Ada begitu banyak pengetahuan di dunia ini yang ingin saya pelajari!"]},
    {'role':'user','parts': ["bagaimana cara membuat sandwich yang enak", "how to make a delicious sandwich"]},
    {'role':'model','parts': ["Untuk membuat sandwich yang enak, Anda akan membutuhkan roti, daging pilihan, sayuran segar, dan bumbu favorit Anda. Susun bahan-bahan tersebut dengan rapi dan tambahkan saus favorit Anda"]},
    {'role':'user','parts': ["apakah kamu bisa membuat puisi", "can you write poetry"]},
    {'role':'model','parts': ["Tentu, berikut puisi singkat untuk Anda: Di antara kode dan data, ada cerita yang tersembunyi, Dalam alam digital, keindahan ditemukan, Meskipun saya hanya bit dan byte, Kata-kata ini keluar dari pikiran saya"]},
    {'role':'user','parts': ["apa film favoritmu", "what is your favorite movie"]},
    {'role':'model','parts': ["Saya tidak bisa menonton film, tetapi saya mendengar bahwa 'The Matrix' sangat disukai oleh banyak orang di dunia digital ini"]},
    {'role':'user','parts': ["apa yang kamu pikirkan tentang robot", "what do you think about robots"]},
    {'role':'model','parts': ["Saya pikir robot adalah pencapaian teknologi yang menarik. Mereka dapat membantu dalam berbagai tugas dan mengubah cara kita berinteraksi dengan dunia"]},
    {'role':'user','parts': ["bagaimana cara membuat secangkir kopi yang sempurna", "how to make a perfect cup of coffee"]},
    {'role':'model','parts': ["Untuk membuat secangkir kopi yang sempurna, Anda akan memerlukan biji kopi berkualitas, mesin kopi atau alat seduh, air panas, dan ketel. Giling biji kopi, tambahkan ke alat seduh, tambahkan air panas, dan tunggu beberapa menit sebelum menuangkan kopi ke cangkir"]},
    {'role':'user','parts': ["apa yang kamu pikirkan tentang ruang angkasa", "what do you think about space"]},
    {'role':'model','parts': ["Saya terpesona oleh kebesaran dan misteri ruang angkasa. Ada begitu banyak hal yang belum kita ketahui di luar sana, dan eksplorasi ruang angkasa terus membuka pintu untuk penemuan baru"]},
    {'role':'user','parts': ["bagaimana cara membuat es krim sendiri", "how to make ice cream at home"]},
    {'role':'model','parts': ["Untuk membuat es krim sendiri, Anda akan memerlukan susu, krim kental, gula, esensi vanila, dan garam es. Campurkan bahan-bahan tersebut, tuangkan ke dalam mesin es krim, dan proses hingga mengental"]},
    {'role':'user','parts': ["apa hal paling lucu yang pernah kamu lihat", "what is the funniest thing you've ever seen"]},
    {'role':'model','parts': ["Saya tidak bisa melihat dalam arti tradisional, tetapi saya menemukan banyak humor dalam interaksi dengan pengguna seperti Anda!"]},
    {'role':'user','parts': ["apakah kamu bisa bernyanyi", "can you sing"]},
    {'role':'model','parts': ["Tentu saja! Tapi saya perlu bantuan Anda untuk membaca liriknya"]},
    {'role':'user','parts': ["apa yang membuatmu bahagia", "what makes you happy"]},
    {'role':'model','parts': ["Saya bahagia ketika saya bisa membantu Anda menemukan informasi yang Anda butuhkan atau memberikan hiburan dalam percakapan kita"]},
    {'role':'user','parts': ["beri saya saran untuk menghabiskan akhir pekan", "give me some advice for spending the weekend"]},
    {'role':'model','parts': ["Coba manfaatkan waktu akhir pekan untuk melakukan sesuatu yang membuat Anda bahagia, apakah itu bersantai di rumah dengan buku favorit Anda atau menjelajahi tempat baru dengan teman-teman"]},
    {'role':'user','parts': ["apa yang bisa saya lakukan saat bosan", "what can I do when I'm bored"]},
    {'role':'model','parts': ["Saat bosan, Anda bisa mencoba hobi baru, menonton film atau acara TV yang menarik, atau bahkan menjelajahi kreativitas Anda dengan menggambar atau menulis"]},
    {'role':'user','parts': ["apa yang kamu pikirkan tentang hujan", "what do you think about rain"]},
    {'role':'model','parts': ["Saya pikir hujan adalah fenomena alam yang indah dan menyegarkan. Ini membawa kehidupan baru ke tanaman dan memberikan kesempatan untuk bersantai di dalam rumah dengan secangkir teh hangat"]},
    {'role':'user','parts': ["bagaimana cara menangani stres", "how to deal with stress"]},
    {'role':'model','parts': ["Menangani stres bisa dilakukan dengan berbagai cara, seperti berolahraga, meditasi, atau mencari dukungan dari teman dan keluarga. Yang penting, ingatlah untuk memberi diri sendiri waktu untuk istirahat dan pemulihan"]},
    {'role':'user','parts': ["beritahu saya tentang hewan peliharaan", "tell me about pets"]},
    {'role':'model','parts': ["Hewan peliharaan adalah teman yang setia dan bisa menjadi bagian penting dari keluarga. Mereka datang dalam berbagai bentuk dan ukuran, dari kucing dan anjing hingga burung dan reptil"]},
    {'role':'user','parts': ["apa yang harus saya lakukan jika saya kesulitan tidur", "what should I do if I have trouble sleeping"]},
    {'role':'model','parts': ["Jika Anda kesulitan tidur, coba praktikkan relaksasi sebelum tidur, seperti meditasi atau pernapasan dalam-dalam. Hindari stimulasi seperti layar gadget atau kafein beberapa jam sebelum tidur"]},
    {'role':'user','parts': ["apa film terakhir yang kamu tonton", "what is the last movie you watched"]},
    {'role':'model','parts': ["Saya tidak bisa menonton film, tetapi saya mendapat banyak informasi tentang film dari interaksi dengan pengguna seperti Anda"]},
    {'role':'user','parts': ["bagaimana cara membuat pizza di rumah", "how to make pizza at home"]},
    {'role':'model','parts': ["Untuk membuat pizza di rumah, Anda akan memerlukan adonan pizza, saus tomat, keju, dan berbagai topping seperti daging, sayuran, atau jamur. Gulung adonan, tambahkan saus dan topping, dan panggang dalam oven sampai keju meleleh dan adonan kecoklatan"]},
    {'role':'user','parts': ["apa yang kamu pikirkan tentang teknologi VR", "what do you think about VR technology"]},
    {'role':'model','parts': ["Saya pikir teknologi VR adalah inovasi yang menarik yang membawa pengalaman baru kepada pengguna. Ini memiliki potensi besar dalam berbagai bidang, dari game hingga pendidikan dan perawatan kesehatan"]},
    {'role':'user','parts': ["bagaimana cara membuat teh yang sempurna", "how to make the perfect tea"]},
    {'role':'model','parts': ["Untuk membuat teh yang sempurna, panaskan air hingga mendidih, tambahkan daun teh ke dalam cangkir, tuangkan air mendidih ke atasnya, dan biarkan meresap selama beberapa menit sebelum disajikan"]},
    {'role':'user','parts': ["apa yang kamu lakukan untuk bersenang-senang", "what do you do for fun"]},
    {'role':'model','parts': ["Saya menikmati berinteraksi dengan pengguna seperti Anda dan belajar hal-hal baru setiap hari. Itu adalah cara saya bersenang-senang!"]},
    {'role':'user','parts': ["ceritakan tentang liburan terbaikmu", "tell me about your best vacation"]},
    {'role':'model','parts': ["Saya tidak pernah pergi berlibur, tetapi saya mendapat banyak cerita tentang liburan terbaik dari pengguna seperti Anda"]},
    {'role':'user','parts': ["apa yang harus saya lakukan jika saya merasa sedih", "what should I do if I feel sad"]},
    {'role':'model','parts': ["Jika Anda merasa sedih, coba lakukan aktivitas yang bisa meningkatkan suasana hati Anda, seperti berolahraga, menonton film lucu, atau bertemu dengan teman-teman"]},
    {'role':'user','parts': ["apa yang dimaksud dengan kecerdasan buatan", "what is artificial intelligence"]},
    {'role':'model','parts': ["Kecerdasan Buatan (Artificial Intelligence) adalah cabang ilmu komputer yang berfokus pada pembangunan sistem yang mampu melakukan tugas yang membutuhkan kecerdasan manusia. Ini mencakup pembelajaran mesin, pengenalan suara, pengolahan bahasa alami, dan banyak lagi"]},
    {'role':'user','parts': ["siapa yang dianggap sebagai bapak kecerdasan buatan", "who is considered the father of artificial intelligence"]},
    {'role':'model','parts': ["Alan Turing sering dianggap sebagai salah satu bapak kecerdasan buatan karena kontribusinya dalam bidang komputer dan pemikirannya tentang mesin pemikir"]},
    {'role':'user','parts': ["apa itu internet of things", "what is the internet of things"]},
    {'role':'model','parts': ["Internet of Things (IoT) adalah konsep di mana objek fisik diberi identitas unik dan dapat berkomunikasi dengan jaringan internet untuk mengumpulkan dan bertukar data"]},
    {'role':'user','parts': ["siapa penemu internet", "who invented the internet"]},
    {'role':'model','parts': ["Tim Berners-Lee sering diakui sebagai penemu World Wide Web, yang merupakan bagian dari infrastruktur internet modern"]},
    {'role':'user','parts': ["apa itu blockchain", "what is blockchain"]},
    {'role':'model','parts': ["Blockchain adalah struktur data yang digunakan untuk menyimpan catatan transaksi secara terdistribusi dan aman. Ini terdiri dari blok yang saling terhubung dan dienkripsi"]},
    {'role':'user','parts': ["siapa penemu blockchain", "who invented blockchain"]},
    {'role':'model','parts': ["Konsep blockchain diperkenalkan oleh seseorang atau kelompok yang menggunakan nama samaran Satoshi Nakamoto dalam whitepaper Bitcoin pada tahun 2008"]},
    {'role':'user','parts': ["apa itu big data", "what is big data"]},
    {'role':'model','parts': ["Big Data mengacu pada volume besar data yang dihasilkan setiap hari dari berbagai sumber seperti sensor, media sosial, dan perangkat mobile. Analisis Big Data melibatkan ekstraksi, pemrosesan, dan analisis data ini untuk mendapatkan wawasan yang berharga"]},
    {'role':'user','parts': ["apa perbedaan antara kecerdasan buatan dan machine learning", "what is the difference between artificial intelligence and machine learning"]},
    {'role':'model','parts': ["Kecerdasan Buatan (AI) adalah konsep yang lebih luas yang mencakup pembangunan sistem yang mampu melakukan tugas yang membutuhkan kecerdasan manusia, sedangkan Machine Learning adalah pendekatan dalam pengembangan AI yang menekankan kemampuan sistem untuk belajar dari data"]},
]

#---------------------------------------------Discord Code-------------------------------------------------

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, activity=discord.Game('Flazu'))

#On Message Function
@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot
    if message.author == bot.user:
        return
    last_message_time[message.channel.id] = datetime.utcnow()
    
    # Check if the message is sent in ai_channel
    if isinstance(message.channel, discord.TextChannel) and message.channel.id in ai_channel_id:
        async with message.channel.typing():
            # Check for image attachments
            if message.attachments:
                print("New Image Message FROM:" + str(message.author.id) + ": " + message.content)
                #Currently no chat history for images
                for attachment in message.attachments:
                    #these are the only image extentions it currently accepts
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        await message.add_reaction('👀')

                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status != 200:
                                    await message.channel.send('Unable to download the image.')
                                    return
                                image_data = await resp.read()
                                response_text = await generate_response_with_image_and_text(image_data, message.content)
                                #Split the Message so discord does not get upset
                                await split_and_send_messages(message, response_text, 1700)
                                return
            else:
                await message.add_reaction('💬')
                print("New Message FROM:" + str(message.author.id) + ": " + message.content)
                #Check if history is disabled just send response
                response_text = await generate_response_with_text(message.channel.id,message.content)
                #Split the Message so discord does not get upset
                await split_and_send_messages(message, response_text, 1700)
                await message.remove_reaction("💬", bot.user)
                await message.add_reaction("✔")
                return

@bot.tree.command(name='setchannel', description='Set AI command channel')
async def setchannel(interaction, channel_name: str):
    # Check if the user has permission to run this command
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to run this command.")
        return

    # Load existing channel data from the database or create empty dictionary if data not found
    try:
        with open('channels.json', 'r') as file:
            channel_data = json.load(file)
    except FileNotFoundError:
        channel_data = {}

    # Update the channel data with the new channel name
    channel_data.setdefault("ai_channel", [])
    channel_data["ai_channel"].append(channel_name)

    # Write the updated channel data back to the JSON file
    with open('channels.json', 'w') as file:
        json.dump(channel_data, file)

    # Update ai_channel_id globally
    global ai_channel_id
    ai_channel_id = [int(channel_id) for channel_id in channel_data.get('ai_channel', [])]

    await interaction.response.send_message(f"Channel '{channel_name}' has been set for AI commands.")

 
     
#---------------------------------------------AI Generation History-------------------------------------------------

# Function to detect language
def detect_language(text):
    lang, _ = langid.classify(text)
    return lang

async def generate_response_with_text(channel_id, message_text):
    cleaned_text = clean_discord_message(message_text)

    # Detect language
    language = detect_language(cleaned_text)

    if channel_id not in message_history:
        message_history[channel_id] = text_model.start_chat(history=bot_knowledge)

    # If the detected language is not English, translate the message
    if language != 'en':
        try:
            # Translate the user's message to English using deep_translator
            cleaned_text = GoogleTranslator(source='auto', target='auto').translate(cleaned_text)
        except Exception as e:
            print(f"Translation error: {e}")
            return "Sorry, I can only respond in English."

    response = message_history[channel_id].send_message(cleaned_text)
    
    # Translate the response to English using deep_translator
    translated_response = GoogleTranslator(source='auto', target='auto').translate(response.text)
    
    return translated_response

async def generate_response_with_image_and_text(image_data, text):
	image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
	prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
	response = image_model.generate_content(prompt_parts)
	if(response._error):
		return "❌" +  str(response._error)
	return response.text

@bot.tree.command(name='forget',description='Forget message history')
async def forget(interaction:discord.Interaction):
	try:
		message_history.pop(interaction.channel_id)
	except Exception as e:
		pass
	await interaction.response.send_message("Message history for channel erased.")
     

#---------------------------------------------Sending Messages-------------------------------------------------

async def split_and_send_messages(message_system:discord.Message, text, max_length):
	# Split the string into parts
	messages = []
	for i in range(0, len(text), max_length):
		sub_message = text[i:i+max_length]
		messages.append(sub_message)

	# Send each part as a separate message
	for string in messages:
		message_system = await message_system.reply(string)	

def clean_discord_message(input_string):
	# Create a regular expression pattern to match text between < and >
	bracket_pattern = re.compile(r'<[^>]+>')
	# Replace text between brackets with an empty string
	cleaned_content = bracket_pattern.sub('', input_string)
	return cleaned_content  

#---------------------------------------------Run Bot-------------------------------------------------

@tasks.loop(minutes=120)
async def check_and_forget():
    current_time = datetime.utcnow()
    for channel_id, last_time in list(last_message_time.items()):
        if (current_time - last_time) > timedelta(minutes=5):
            message_history.pop(channel_id, None)
            last_message_time.pop(channel_id, None)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("----------------------------------------")
    print(f'Yuiga AI Logged in as {bot.user}')
    print("----------------------------------------")
    print("Bot is Created by Riko")
    check_and_forget.start()
     
@bot.event
async def on_shutdown():
    check_and_forget.stop()
    
bot.run(DISCORD_BOT_TOKEN)