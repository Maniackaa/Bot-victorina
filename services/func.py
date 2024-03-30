
import datetime
from dataclasses import dataclass

import aiohttp


def get_positive_quality(birthday):
    if birthday is None:
        return None
    if birthday.day + birthday.month > 22:
        result = int(birthday.day + birthday.month - 22)
    else:
        result = int(birthday.day + birthday.month)
    return result


def get_negative_quality(birthday):
    if birthday is None:
        return "Не указан день рождения пользователя"
    year = birthday.year
    qversum = 0
    while year != 0:
        qversum += year % 10
        year //= 10
    if qversum > 22:
        qversum -= 22
    negative_quality = abs(birthday.day - qversum)
    if negative_quality > 22:
        negative_quality -= 22
    result = negative_quality
    return result or 22


def get_hr_conversation(birthday):
    if birthday is None:
        return "Не указан день рождения пользователя"
    form = int(birthday.strftime("%d%m")) * birthday.year
    while len(str(form)) < 7:
        form = form * 10
    if form % 10 < 4:
        return 1
    if form % 10 < 7:
        return 2
    return 3


def get_hr_career(birthday):
    if birthday is None:
        return "Не указан день рождения пользователя"
    strform = str(int(birthday.strftime("%d%m")) * birthday.year)
    sumform = 0
    for h in strform:
        sumform += int(h)
    if sumform < 26:
        return 1
    if sumform < 29:
        return 2
    return 3


def specialist_profit(spec_birthday, company_registration):  # day format ddmmyyyy
    spec_birthday = spec_birthday.strftime('%d%m%Y')
    print(spec_birthday)
    company_registration = company_registration.strftime('%d%m%Y')
    spec_num = int(spec_birthday[:4]) * int(spec_birthday[4:])
    comp_num = int(company_registration[:4]) * int(company_registration[4:])
    gkz = 0
    while spec_num != 0:
        gkz += spec_num % 10
        spec_num //= 10
    while comp_num != 0:
        gkz += comp_num % 10
        comp_num //= 10

    while gkz > 22:
        gkz -= 22

    if gkz == 1:
        return 18
    elif gkz == 2:
        return 9
    elif gkz == 3:
        return 27
    elif gkz == 4:
        return 90
    elif gkz == 5:
        return 36
    elif gkz == 6:
        return 23
    elif gkz == 7:
        return 41
    elif gkz == 8:
        return 54
    elif gkz == 9:
        return 32
    elif gkz == 10:
        return 99
    elif gkz == 11:
        return 50
    elif gkz == 12:
        return 5
    elif gkz == 13:
        return 72
    elif gkz == 14:
        return 95
    elif gkz == 15:
        return 77
    elif gkz == 16:
        return 81
    elif gkz == 17:
        return 68
    elif gkz == 18:
        return 14
    elif gkz == 19:
        return 86
    elif gkz == 20:
        return 59
    elif gkz == 21:
        return 63
    elif gkz == 22:
        return 45
    else:
        return gkz


async def post_aiohttp_response(url, response_type='text', headers=None, params=None, data=None, cookies=None,
                                cookie_jar=aiohttp.CookieJar(unsafe=True), ssl=False):
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with session.post(url,
                                headers=headers,
                                params=params,
                                cookies=cookies,
                                ssl=ssl,
                                data=data) as response:
            if response.status == 200:
                if response_type == 'json':
                    result = await response.json(content_type='text/html', encoding='UTF-8')
                elif response_type == 'text':
                    result = await response.text(encoding='UTF-8')
                return result
            else:
                raise ConnectionError('Неверный ответ от сервера')


def main():
    start = datetime.date(1900, 1, 1)
    index1 = set()
    index2 = set()
    index3 = set()
    index4 = set()
    index5 = set()
    for i in range(0, 36500):
        birthday = start + datetime.timedelta(i)
        # print(birthday)
        positive_index = get_positive_quality(birthday)
        negative_index = get_negative_quality(birthday)
        hr_conversation_index = get_hr_conversation(birthday)
        hr_career_index = get_hr_career(birthday)
        specialist_profit_index = specialist_profit(birthday, datetime.date(2023, 1, 1))
        index1.add(positive_index)
        index2.add(negative_index)

        if negative_index == 0:
            print(birthday)
            # break
        index3.add(hr_conversation_index)
        index4.add(hr_career_index)
        index5.add(specialist_profit_index)
        # print(positive_index, negative_index, hr_conversation_index, hr_career_index)
    print(index1)
    print(index2)
    print(index3)
    print(index4)
    print(index5)
if __name__ == '__main__':
    main()


