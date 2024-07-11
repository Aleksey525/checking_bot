from environs import Env
import requests
import telegram
import time


RECONNECTION_DELAY = 30


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_BOT_TOKEN')
    bot = telegram.Bot(token=bot_token)
    devman_token = env.str('DEVMAN_TOKEN')
    chat_id = env.str('TG_CHAT_ID')
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


if __name__ == '__main__':
    main()
