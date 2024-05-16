import telebot
from info import start_info, official
from keyboards import start_keyboard, menu_keyboard
from creds import get_bot_token, get_creds
import requests
import logging
import sqlite3

#iam_token, folder_id = get_creds()
#не работает

iam_token = "t1.9euelZrPjpOTzJyNl46Tj5bNyMrJie3rnpWakpqbiZeUmZScz5GSlsaNxsvl8_cnEGdN-e9MPmBo_t3z92c-ZE3570w-YGj-zef1656VmpfPmJSMioyKypKZkMeckpeR7_zF656VmpfPmJSMioyKypKZkMeckpeRveuelZqNnpHGyo-PjIzGy4rNmpjGm7XehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.fi4DJ77L4eaNieu7rHb1lP3iIH7MAJJAAWiJ5SENu5Rqa1-WXH8Wm87jw3t-sA-K6Nap1m3w00RIgqQke-NVBQ"
folder_id = 'b1g5aqf2rl8hk0garevb'


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",
)

token = "6829420719:AAE-TzSX233dOWezfLEsUZe94c2Uwve638g"
bot = telebot.TeleBot(token)
print(bot.get_me())


con = sqlite3.connect('datbasaaa.bd')
cur = con.cursor()
quer = f'''
CREATE TABLE IF NOT EXISTS AIN(
    user_id INTEGER PRIMARY KEY,
    tts_s INTEGER, 
    stt_s INTIGER, 
    stt_b INTEGER, 
    sessions INTEGER
);
'''
cur.execute(quer)
con.close()


@bot.message_handler(commands=['start'])
def handle_start(message):
    logging.info("Отправка приветственного сообщения")
    bot.send_message(message.chat.id, start_info, reply_markup=menu_keyboard)


@bot.message_handler(content_types=["text"])
def question(message):
    if message.text.lower() == "задать вопрос gpt":
        logging.info("Пользователь хочет задать вопрос")
        bot.send_message(message.chat.id, "Напишите вопрос или отправьте аудио")
        bot.register_next_step_handler(message, answer)


@bot.message_handler(content_types=["text"])
def answer(message):
    if not message.voice and not message.text:
        logging.info("Пользователь отправил не текст и не аудио")
        bot.send_message(message.chat.id, "Напишите вопрос или отправьте аудио")
        bot.register_next_step_handler(message, answer)
    else:
        if message.text:
            logging.info("Пользователь отправил текст")
            global text
            text = message.text
            bot.register_next_step_handler(message, answer1)
            global audi
            audi = False

        elif message.voice:
            logging.info("Пользоватеь отправил аудио")

            audi = True

            file_id = message.voice.file_id
            file_info = bot.get_file(file_id)
            global file
            file = bot.download_file(file_info.file_path)
            global stt_blocks
            stt_blocks = int(message.voice.duration) // 15 + 1

            if stt_blocks > 2:
                bot.send_message(message.chat.id, "Сообщение слишком большое")
                bot.register_next_step_handler(message, handle_start)

            elif stt_blocks <= 2:
                bot.register_next_step_handler(message, speech_to_text)


def speech_to_text(message):

    logging.info('2')

    params = "&".join([
        "topic=general",
        f"folderId={folder_id}",
        f"lang=ru-RU"
    ])

    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }

    # Выполняем запрос
    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=file
    )
    logging.info('3')

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        logging.info("Раскод")
        global text
        text = decoded_data.get("result")
        stt_s = len(text)
        tts_s = len(text)
        con = sqlite3.connect('datbasaaa.bd')
        cur = con.cursor()
        quer = f'''
            INSERT OR REPLACE INTO AIN (user_id, tts_s, stt_s, stt_b, sessions)
            VALUES ("{message.from_user.id}", "{tts_s}", "{stt_s}", "{stt_blocks}", "?");
        '''
        cur.execute(quer)
        con.commit()
        con.close()
        bot.register_next_step_handler(message, answer1)
    else:
        # Если возникла ошибка, выводим сообщение об ошибке
        logging.error('Ошибка кода')
        bot.send_message(message.chat.id, "Ошибка при выполнении запроса, приношу свои извенения(")


def answer1(message):
    # Выполняем запрос к YandexGPT
    logging.info("Фаза GPT")

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",  # модель для генерации текста
        "completionOptions": {
            "stream": False,  # потоковая передача частично сгенерированного текста выключена
            "temperature": 0.6,
            # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
            "maxTokens": "200"
            # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
        },
        "messages": [
            {
                "role": "assistant",
                "text": 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'
            },
            {
                "role": "user",  # пользователь спрашивает у модели
                "text": text  # передаём текст, на который модель будет отвечать
            }
        ]
    }
    logging.info("Фаза прошла успешно")

    # Выполняем запрос к YandexGPT
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                             headers=headers,
                             json=data)

    if response.status_code == 200:
        logging.info("Ответ был успешно сгенерирован")
        global result
        result = response.json()["result"]["alternatives"][0]["message"]["text"]

        if audi == False:
            bot.send_message(message.chat.id, result)
            logging.info("Ответ был успешно отправлен")
        elif audi == True:
            bot.register_next_step_handler(message, text_to_speech)
            logging.info("Форматирую аудио")
    else:
        logging.error("Не удалось сгенерировать ответ")
        bot.reply_to(message, "Извини, я не смог сгенерировать для тебя ответ")


def text_to_speech(message):

    logging.info("Проверка на длину")
    if len(text) > 50:
        logging.info("Большое сообщение")
        bot.send_message(message.chat.id, 'Сообщение слишком большое!!! Отправьте его заново')
        bot.register_next_step_handler(message, text_to_speech)

    else:
        logging.info("Проверка прошла успешно")
        headers = {
        'Authorization': f'Bearer {iam_token}',
        }
        logging.info("1")
        data = {
            'text': result,  # текст, который нужно преобразовать в голосовое сообщение
            'lang': 'ru-RU',  # язык текста - русский
            'voice': 'filipp',  # голос Филлипа
            'folderId': folder_id,
        }
        logging.info("2")
        # Выполняем запрос
        response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)
        logging.info("3")

        if response.status_code == 200:
            response = response.content
            logging.info("Код 200")
            with open("output.ogg", "wb") as audio_file:
                audio_file.write(response)
            bot.send_audio(message.chat.id, response)
            logging.info('Аудио было отправлено успешно')

        else:
            # Если возникла ошибка, выводим сообщение об ошибке
            logging.error('Ошибка кода')
            bot.send_message(message.chat.id, "Ошибка при выполнении запроса, приношу свои извенения(")






if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.polling()