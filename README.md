# Bot-victorina

Переменуйте .env.example в .env и заполните переменные 
GROUP_ID - ID группы
BOT_TOKEN - токен бота
ADMIN_IDS= - список админов через запятую
TABLE_1 - гугл таблица с данными 

### Установка:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Maniackaa/Bot-victorina.git
```

```
cd Bot-victorina
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
./venv/bin/activate.bat
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```


Запустить проект:

```
python __main__.py
```