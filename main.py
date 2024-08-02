import logging
import requests
import time

from environs import Env
import telegram


RECONNECTION_DELAY = 30
ERROR_CHECKING_DELAY = 10

logger = logging.getLogger('Logger')


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_BOT_TOKEN')
    bot_logger_token = env.str('TG_LOGGER_BOT_TOKEN')
    bot = telegram.Bot(token=bot_token)
    logger_bot = telegram.Bot(token=bot_logger_token)
    chat_id = env.str('TG_CHAT_ID')
    devman_token = env.str('DEVMAN_TOKEN')
    logger.setLevel(logging.DEBUG)
    telegram_handler = TelegramLogsHandler(logger_bot, chat_id)
    telegram_handler.setLevel(logging.DEBUG)
    logger.addHandler(telegram_handler)
    logger.info('Бот запущен')
    timestamp = ''
    while True:
        try:
            url_long_polling = 'https://dvmn.org/api/long_polling/'
            params = {'timestamp': timestamp}
            headers = {'Authorization': devman_token}
            response = requests.get(url_long_polling, headers=headers, proxies=params, timeout=120)
            response.raise_for_status()
            attempts = response.json()
            verification_status = attempts['status']
            if verification_status == 'found':
                new_attempts = attempts['new_attempts']
                for attempt in new_attempts:
                    timestamp = attempt['timestamp']
                    lesson_title = attempt['lesson_title']
                    lesson_url = attempt['lesson_url']
                    result_checking = attempt['is_negative']
                    bot.send_message(text=f'У вас проверили работу «{lesson_title}»\n'
                                          f'{lesson_url}', chat_id=chat_id)
                    if result_checking:
                        bot.send_message(text=f'К сожалению, в работе нашлись ошибки',
                                         chat_id=chat_id)
                    else:
                        bot.send_message(text=f'Преподавателю всё понравилось можно приступать к следующему уроку',
                                         chat_id=chat_id)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(RECONNECTION_DELAY)
        except Exception as err:
            logger_bot.send_message(chat_id=chat_id, text='Бот упал с ошибкой:')
            logger.error(err, exc_info=True)
            time.sleep(ERROR_CHECKING_DELAY)


if __name__ == '__main__':
    main()
