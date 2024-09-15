import os
import logging
import requests

from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(level=logging.DEBUG)

s = requests.Session()

retries = Retry(
    total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
)

s.mount("https://", HTTPAdapter(max_retries=retries))


def make_phone_call(phone: str, ip: str):
    """
    Sends a request to make a call to a number
    :param phone: str
    :param ip: str (user ip address)
    :return: str or None (last 4 digits of the phone number from which the call will be made)

    source: https://sms.ru/api/code_call
    """

    # FIXME: При передаче ip адреса клиента вызывала ошибку что запрос сделан из частной сети,
    #  необходимо отправить запрос в смс.ру с уточнением причины, пока установлен параметр
    #  -1 как отправка звонка вручную
    params = {"api_id": os.environ["SMS_RU_API_ID"], "phone": phone, "ip": -1}

    result = s.get(url="https://sms.ru/code/call", params=params)
    data = result.json()

    status = data.get("status")

    if status == "OK":
        return str(data.get("code"))
    elif status == "ERROR":
        raise ValueError(data.get("status_text", ""))
    else:
        raise Exception("Ошибка API sms.ru")
