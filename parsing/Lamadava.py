import json

import requests

from config import TOKEN
from logger import logger
from .Parser import Parser

logger_lamadava = logger("__lamadava__")


class Lamadava(Parser):

    def __init__(self):
        self.token = TOKEN
        headers = {
            'accept': 'application/json',
            'x-access-key': self.token
        }
        self.session = requests.Session()
        self.session.headers = headers

    def get_user_info(self, username) -> list:
        response = self.session.get(url=f"https://api.lamadava.com/a1/user?username={username}")
        try:
            data = json.loads(response.text)
            print(data)
            if "graphql" in data:
                user = data["graphql"]["user"]
            elif "detail" in data:
                logger_lamadava.error(f"| the server did not return information about {username} | {response.text}")
                return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
            elif "state" in data:
                logger_lamadava.error(f"| {username} | {response.text}")
                return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
            else:
                logger_lamadava.critical(f"| {username} | {response.text}")
                return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
        except json.decoder.JSONDecodeError as ex:
            logger_lamadava.critical(f"| {ex} | {username} | {response.text}", exc_info=True)
            return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
        except Exception as ex:
            logger_lamadava.critical(f"| {ex} | {username}", exc_info=True)
            return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
        else:
            fullname = self.remove_formatting(user["full_name"])
            first_name = fullname.split()[0] if len(fullname.split()) == 2 else ""
            email = user['business_email'] if user['business_email'] else self.find_email(user['biography'])
            phone = user["business_phone_number"] if user["business_phone_number"] \
                else self.find_phone_number(user['biography'])
            return [first_name, username, fullname, email, phone, f'https://www.instagram.com/{username}/',
                    str(user['edge_followed_by']['count'])]
