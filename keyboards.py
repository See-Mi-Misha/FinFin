#сюда я убрал все кнопки, чтобы было проще работать в коде
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from info import menu

start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add(KeyboardButton('Да'))


menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(menu)