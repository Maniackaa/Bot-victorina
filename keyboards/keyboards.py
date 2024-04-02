from aiogram.types import KeyboardButton, ReplyKeyboardMarkup,\
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def custom_kb(width: int, buttons_dict: dict) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons = []
    for key, val in buttons_dict.items():
        callback_button = InlineKeyboardButton(
            text=key,
            callback_data=val)
        buttons.append(callback_button)
    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()

kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
begin_btn = InlineKeyboardButton(
    text='Учавствовать',
    url='https://t.me/OlditBot'
)
buttons = [begin_btn]
kb_builder.row(*buttons, width=1)
begin_kb = kb_builder.as_markup()



contact_kb_buttons = [
    [KeyboardButton(
        text="Отправить номер телефона",
        request_contact=True
    )],
    ]

contact_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=contact_kb_buttons,
    resize_keyboard=True)


def kb_from_list(kb_buttons, width=1, back='Назад'):
    buttons: list[KeyboardButton] = [KeyboardButton(text=key) for key in kb_buttons]
    if back:
        buttons.append(KeyboardButton(text=back))
    # print(buttons)
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=width)
    menu_kb = kb_builder.as_markup(resize_keyboard=True)
    return menu_kb
