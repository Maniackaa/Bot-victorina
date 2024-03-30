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


start_kb_b = {
    'Аналитика': 'analyse',
    'Компании': 'comp',
    'Помощь': 'help',

}

demo_start_kb_b = {
    'Анализ сотрудника': 'analyse',
}

start_kb = custom_kb(1, start_kb_b)
demo_start_kb = custom_kb(1, demo_start_kb_b)

kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
kb_list = [val for val in start_kb_b.keys()]
buttons: list[KeyboardButton] = [KeyboardButton(text=key) for key in kb_list]
kb_builder.row(*buttons, width=1)
menu_kb = kb_builder.as_markup(resize_keyboard=True)

contact_kb_buttons = [
    [KeyboardButton(
        text="Отправить номер телефона",
        request_contact=True
    )],
    ]

contact_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=contact_kb_buttons,
    resize_keyboard=True)


kb = [
    [KeyboardButton(text="/start")],
    ]
not_auth_start_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True)

kb = [
    [KeyboardButton(text="Анализ сотрудника")],
    ]
auth_start_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True)

# analyse_list = ['Проанализировать сотрудника', 'Проверить совместимость с контрагентом', 'Принять бизнес решение', 'Назад']
analyse_list = ['Проанализировать сотрудника', 'Проверить совместимость с контрагентом', 'Назад']
buttons: list[KeyboardButton] = [KeyboardButton(text=key) for key in analyse_list]
kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
kb_builder.row(*buttons, width=1)
analyse_menu_kb = kb_builder.as_markup(resize_keyboard=True)


def kb_from_list(kb_buttons, width=1, back='Назад'):
    buttons: list[KeyboardButton] = [KeyboardButton(text=key) for key in kb_buttons]
    if back:
        buttons.append(KeyboardButton(text=back))
    # print(buttons)
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=width)
    menu_kb = kb_builder.as_markup(resize_keyboard=True)
    return menu_kb
