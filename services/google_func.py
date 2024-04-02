import asyncio
import dataclasses

import gspread_asyncio
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials

from config_data.bot_conf import BASE_DIR, config, get_my_loggers
from database.db import Coupon

logger, err_log = get_my_loggers()


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    json_file = BASE_DIR / 'credentials.json'
    creds = Credentials.from_service_account_file(json_file)
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


async def load_range_values(url=config.tg_bot.TABLE_1, sheets_num=0, diap='А:A'):
    logger.debug('google')
    agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
    agc = await agcm.authorize()
    url = url
    sheet = await agc.open_by_url(url)
    table = await sheet.get_worksheet(sheets_num)
    values = await table.get_values(diap)
    return values


async def write_to_table(rows: list[list], start_row=1, from_start=False, url=config.tg_bot.TABLE_1,
                          sheets_num=0, delta_col=0):
    """Запись строк в гугл-таблицу
    :param rows: список строк для вставки
    :param start_row: Номер первой строки
    :from_start: Вписывать в начало?
    :param url: адрес таблицы
    :param sheets_num: номер листа
    :param delta_col: смещение по столбцам
    :return:
    """
    try:
        if not rows:
            return
        logger.debug(f'Добавляем c {start_row}: {rows}')
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        agc = await agcm.authorize()
        sheet = await agc.open_by_url(url)
        table = await sheet.get_worksheet(sheets_num)
        # await table.append_rows(rows)
        num_rows = len(rows)
        num_col = len(rows[0])

        if from_start:
            logger.debug(f'Вписываем в начало: {len(rows)} строк')
            await table.insert_rows(values=rows[::-1], row=2)
        else:
            logger.debug(
                f'{rowcol_to_a1(start_row, 1 + delta_col)}:{rowcol_to_a1(start_row + num_rows - 1, num_col + delta_col)}')
            result = await table.batch_update([{
                'range': f'{rowcol_to_a1(start_row, 1 + delta_col)}:{rowcol_to_a1(start_row + num_rows, num_col + delta_col)}',
                'values': rows,
            }])
            # logger.debug(f'{result}')
        return True
    except Exception as err:
        logger.error(err)
        err_log.error(err, exc_info=True)
        raise err


async def load_free_coupons(search_name) -> list[Coupon]:
    table_values = await load_range_values(sheets_num=2, diap='A:F')
    free_cupons = []
    for row in table_values[1:]:
        # print(row)
        num, promo, score, discont, vict_name, status = row
        coupon = Coupon(int(num), promo, int(score), int(discont), vict_name, status)
        # print(num, promo, score, discont, vict_name, status)
        print(coupon)
        if search_name == vict_name and not status:
            free_cupons.append(coupon)
        free_cupons.sort(key=lambda x: -x.score)
    return free_cupons


async def main():
    pass


    # result = await load_range_values(diap='A:G')
    # print(result)
    # free = await load_free_coupons('test_vict')
    # print('result:', free)
    # for c in free:
    #     print(c)
    # await write_to_table(rows=[['xxx']], start_row=7, delta_col=5, sheets_num=2)
    # for key, val in x.items():
    #     print(key, type(key))
        # if key == '1245785663':
        #     print(val)

if __name__ == '__main__':
    asyncio.run(main())


    # for u in y.items():
    #     print(u)
    #     break
    # print(y)
    # asyncio.run(write_stats_from_table())




