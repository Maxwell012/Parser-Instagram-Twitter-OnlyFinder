import random
import re
from time import sleep

import requests

from config import API_KEY_PROXY


# from undetected_chromedriver import Chrome, ChromeOptions


class Parser:

    @staticmethod
    def get_proxies() -> list:
        with requests.Session() as session:
            headers = {"Authorization": f"Token {API_KEY_PROXY}"}
            response = session.get("https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100",
                                   headers=headers)
            if response.status_code == 200:
                proxies = [f"{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['port']}"
                           for proxy in response.json()["results"]]
            else:
                print(f"Failed to get proxy list: {response.status_code}")
        return proxies

    @staticmethod
    def check_proxy(proxy) -> bool:
        """
        Checker for proxy.

        :param proxy: login:password@ip:port or ip:port
        :return: True or False
        """
        proxies = {
            'http': f"http://{proxy}",
            'https': f"http://{proxy}",
        }
        try:
            response = requests.get('https://i.instagram.com/accounts/login/', proxies=proxies)
            if 200 <= response.status_code < 400:
                return True
            else:
                return False
        except Exception:
            return False

    def get_random_proxy(self, proxies: list) -> str | None:
        """
        Get a random proxy after checking, if there is no good proxy then it returns None.

        :param proxies: list that makes up proxy like this username:password@ip:port
        :return: username:password@ip:port or ip:port
        """

        for _ in range(len(proxies)):
            proxy = random.sample(proxies, 1)[0]
            if self.check_proxy(proxy):
                # proxies.remove(proxy)
                return proxy

    @staticmethod
    def timeout(start, end):
        random_number = "{:.2f}".format(random.uniform(start, end))
        sleep(float(random_number))

    # @staticmethod
    # def create_browser(proxy=None) -> Chrome:
    #     options = ChromeOptions()
    #     options.add_argument('--headless')
    #     options.add_argument('--disable-gpu')
    #     if proxy:
    #         options.add_argument(f'--proxy-server={proxy.split("@")[1]}')
    #         options.add_argument(f'--proxy-auth={proxy.split("@")[0]}')
    #     browser = Chrome(options=options, version_main=112)
    #     browser.maximize_window()
    #     return browser

    @staticmethod
    def get_username(url, social_network) -> str:
        return re.search(social_network + r'\.com/([A-Za-z0-9_.]+)', url).group(1)

    @staticmethod
    def find_email(text) -> str | None:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email = re.search(email_regex, text)
        return email.group(0).lower() if email else None

    @staticmethod
    def find_phone_number(text) -> str | None:
        phone_number_regex = r'\+?\d{1,3}\s?(\(|-|\.)?\d{3}(\)|-|\.)?\s?\d{3}(-|\.)?\d{2}(-|\.)?\d{2}'
        matches = re.search(phone_number_regex, text)
        return matches[0] if matches else None

    @staticmethod
    def remove_html_tags(text) -> str:
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def remove_formatting(self, full_name) -> str:
        full_name = self.remove_html_tags(full_name)
        full_name = full_name.replace('_', ' ')
        full_name = re.sub(r'[^A-Za-z0-9\s]+', '', full_name)
        full_name = full_name.strip()
        return full_name
