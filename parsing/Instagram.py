import email
import imaplib
import json
import os
import pickle
import random
import re
import time
from pathlib import Path

from instagrapi import Client
# classes for handling exceptions
from instagrapi.exceptions import (
    UserNotFound,
    ClientError,
    ClientForbiddenError,
    BadPassword,
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RecaptchaChallengeForm,
    ReloginAttemptExceeded,
    SelectContactPointRecoveryForm,
)
# Libs for handling Email/SMS challenges
from instagrapi.mixins.challenge import ChallengeChoice

from logger import logger
from .Parser import Parser


class Instagram(Parser):
    proxies = []
    action = []
    another_function = False
    logger_ = logger("__instagram__")

    def __new__(cls, *args, **kwargs):
        cls.proxies = cls.get_proxies()
        cls.actions = [cls.follow, cls.watch_stories, cls.watch_media]
        return super().__new__(cls)

    def __init__(
            self,
            username: str,
            password: str,
            mail_username: str,
            mail_password: str,
            host: str,  # host for connecting with an email via IMAP
            settings: dict or Path = None,
            proxy: str = None,  # format: http://username:password@ip:port
            delay: int = 0  # 864
    ):
        self.mail_username = mail_username
        self.mail_password = mail_password
        self.host = host
        self.__mail = self.connect_mail()
        self.last_usage = 0
        self.delay = delay
        self.number_failed_attempts = 0

        self.__client = Client()
        self.__client.username = username
        self.__client.password = password

        # SETTINGS
        if isinstance(settings, Path):
            self.__client.load_settings(path=settings)
        else:
            if isinstance(settings, dict):
                self.__client.set_settings(settings=settings)
            else:
                self.__client.login(self.__client.username, self.__client.password)

        # PROXIES
        if proxy:
            self.__client.set_proxy(proxy)
        # else:
        #     self.change_proxy()

        self.__client.challenge_code_handler = self.challenge_code_handler

    def connect_mail(self) -> imaplib.IMAP4_SSL | None:
        try:
            print(f"Connecting to {self.mail_username}", end=" | ")
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.mail_username, self.mail_password)
        except imaplib.IMAP4.error as ex:
            self.logger_.error(f"Error while connecting to email server: {ex}", exc_info=True)
            return self.connect_mail()
        except Exception as ex:
            self.logger_.error(f"Unexpected error while connecting to email server: {ex}", exc_info=True)
            raise ex
        else:
            print(f"Connection is successful")
            return mail

    def save_settings(self):
        """
        the login settings are saving to parsing/settings/'instagram_username'/settings.json
        the login data is saving to parsing/settings/'instagram_username'/data.json
        """

        directory = f"parsing/settings/{self.__client.username}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.__client.dump_settings(Path(f"{directory}/settings.json"))
        with open(f"{directory}/data.json", "w") as file:
            dict_ = {"instagram": {"username": self.__client.username, "password": self.__client.password},
                     "mail": {"username": self.mail_username, "password": self.mail_password, "host": self.host},
                     "proxy": f"{self.__client.proxy}"}
            if self.__client.proxy:
                dict_["proxy"] = self.__client.proxy
            json.dump(dict_, file)
        print("\tCreated settings")

    def rebuild_client_settings(self):
        cookies = self.__client.cookie_dict
        with open("parsing/devices.pkl", "rb") as file:
            devices = pickle.load(file)
        device = devices.pop(0)
        with open("parsing/devices.pkl", "wb") as file:
            pickle.dump(devices, file)
        return {"cookies": cookies, **device}

    def change_proxy(self):
        # if self.proxies:
        #     proxy = self.get_random_proxy(proxies=self.proxies)
        # else:
        #     self.proxies = self.get_proxies()
        #     proxy = self.get_random_proxy(proxies=self.proxies)
        proxy = self.get_random_proxy(proxies=self.proxies)
        if proxy:
            result = self.__client.set_proxy(f"http://{proxy}")
            if result:
                print(f"SET PROXY: {proxy} for {self.__client.username}")
            else:
                print(f"PROXY WAS NOT SET")
        else:
            print(f"THERE IS NOT A GOOD PROXY")

    def check_last_usage(self):
        """check the pause between requests, if the pause is not yet fully executed then the account goes to sleep"""

        if 3 < (time.time() - self.last_usage) <= self.delay:
            time_resume = self.last_usage + self.delay
            print(f"PAUSE, the script will resume at {time.strftime('%H:%M:%S', time.localtime(time_resume))}")
            time.sleep(self.delay - (time.time() - self.last_usage))

    def get_time_available(self) -> float:
        return self.delay - (time.time() - self.last_usage)

    def get_user_info(self, username: str) -> list | None:
        self.check_last_usage()
        print(f"({self.__client.username})", end=" ")
        try:
            user = self.__client.user_info_by_username_gql(username)
        except UserNotFound:
            print(f"INSTAGRAM: {username} was not found, most likely this account is blocked")
            return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
        except ChallengeRequired as ex:
            self.logger_.error(f"CHALLENGE REQUIRED (need to log in manually): {ex}")
            # self.change_proxy()
        except LoginRequired as ex:
            self.logger_.error(f"LOGIN REQUIRED: {ex}")
            # self.timeout(14400, 15000)
            self.__client.relogin()
        except ClientError as ex:
            if ex.code == 404 or "Not Found for url" in ex.message:
                print(f"INSTAGRAM: {username} was not found, most likely this account is blocked")
                return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
            else:
                self.logger_.error(f"| {ex.code} | CLIENT ERROR: {ex}")
                # self.client.relogin()
                self.change_proxy()
                # self.get_user_info(username)
                # self.timeout(14400, 15000)
        except KeyError:
            print("In order to see this profile you must be 18 years old")
            return [None, username, None, None, None, f'https://www.instagram.com/{username}/', None]
        except Exception as ex:
            self.logger_.critical(f"CRITICAL ERROR: {ex}")
            if "Please wait a few minutes before you try again" in str(ex) or "too many 429 error responses" in str(ex):
                match self.number_failed_attempts:
                    case 0:
                        self.delay = 1800
                    case 1:
                        self.delay = 3600
                    case 2:
                        self.delay = 9000
                    case _:
                        self.delay = 27000
                self.number_failed_attempts += 1
                print(f"SET UP THE DELAY FOR {self.delay}s")
        else:
            # if not user.is_private:
            #     amount = random.randint(1, 2)
            #     for _ in range(amount):
            #         function = random.choice(self.actions)
            #         function(user.pk)

            fullname = self.remove_formatting(user.full_name)
            first_name = fullname.split()[0] if len(fullname.split()) == 2 else None

            if user.public_email:
                email_ = user.public_email
            else:
                bio = user.biography
                email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_ = re.findall(email_regex, bio)
                match len(email_):
                    case 0:
                        email_ = None
                    case 1:
                        email_ = email_[0]
                    case 2:
                        email_ = "\n".join(email_)

            phone = user.public_phone_number if user.public_phone_number else None

            result = [first_name, username, fullname, email_, phone, f'https://www.instagram.com/{username}/',
                      str(user.follower_count)]

            if self.delay > 864:
                self.delay = 864
                self.number_failed_attempts = 0

            return result
        finally:
            self.last_usage = time.time()

    # ACTIONS

    def follow(self, user_id: str):
        try:
            self.__client.user_follow(user_id)
            print("Followed | ", end="")
        except ClientForbiddenError:
            self.logger_.error(" | follow | ClientForbiddenError")

    def watch_stories(self, user_id: int):
        try:
            stories = self.__client.user_stories(int(user_id), amount=random.randint(1, 4))
            story_pks = [int(story.pk) for story in stories]
            self.__client.story_seen(story_pks)
            print("Watched_stories | ", end="")

            list_ = [True, False]
            if stories:
                if random.choices(list_, weights=[0.2, 0.8], k=1)[0]:
                    self.leave_like_story(random.choice(stories).id)
        except ClientForbiddenError:
            self.logger_.error("| watch_stories | ClientForbiddenError")

    def watch_media(self, user_id: int):
        try:
            medias = self.__client.user_medias(int(user_id), amount=random.randint(1, 10), sleep=random.randint(1, 3))
            media_ids = [media.id for media in medias]
            self.__client.media_seen(media_ids)
            print("Watched_media | ", end="")

            list_ = [True, False]
            if media_ids:
                if random.choices(list_, weights=[0.2, 0.8], k=1)[0]:
                    self.leave_like_media(random.choice(media_ids))
        except ClientForbiddenError:
            self.logger_.error("| watch_media | ClientForbiddenError")

    def leave_like_media(self, media_id: str):
        self.__client.media_like(media_id, revert=True)
        print("Liked_media | ", end="")

    def leave_like_story(self, story_id: str):
        self.__client.story_like(story_id, revert=True)
        print("Liked_story | ", end="")

    # CHALLENGE_CODE_HANDLER

    def get_code_from_email(self, username: str):
        try:
            self.__mail.select("inbox")
            result, data = self.__mail.search(None, "(UNSEEN)")
            if result == "command: SELECT => Disconnected for inactivity.":
                self.connect_mail()
            elif result != "OK":
                raise Exception(f"Error during get_code_from_email: {result}")

            ids = data.pop().split()
            for num in reversed(ids):
                self.__mail.store(num, "+FLAGS", "\\Seen")
                result, data = self.__mail.fetch(num, "(RFC822)")
                print(result)
                if result != "OK":
                    raise Exception(f"Error during get_code_from_email: {result}")

                msg = email.message_from_string(data[0][1].decode())
                payloads = msg.get_payload()
                if not isinstance(payloads, list):
                    payloads = [msg]

                for payload in payloads:
                    body = payload.get_payload(decode=True).decode()

                    if "<div" not in body:
                        continue
                    if username not in body:
                        continue

                    match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)
                    if match:
                        match = re.search(r">(\d{6})<", body)
                        if not match:
                            print('Skip this email, "code" not found')
                            continue

                        code = match.group(1)
                        if code:
                            print(f"Instagram code found in email: {code}")
                            return code
                    else:
                        continue

            print("No new emails with Instagram code found")
            return False

        except Exception as e:
            self.logger_.error(f"Error during get_code_from_email: {str(e)}")
            if str(e) in ["command: SELECT => Disconnected for inactivity.", "command: SELECT => socket error: EOF",
                          "socket error: TLS/SSL connection has been closed (EOF) (_ssl.c:2393)"]:
                self.connect_mail()
            return False

    def get_code_from_sms(self):
        while True:
            code = input(f"Enter code (6 digits) for {self.__client.username}: ").strip()
            if code and code.isdigit():
                return code

    def challenge_code_handler(self, username: str, choice=None):
        if choice == ChallengeChoice.SMS:
            return self.get_code_from_sms()
        elif choice == ChallengeChoice.EMAIL:
            return self.get_code_from_email(username)
        return False

    # HANDLE_EXCEPTION

    def handle_exception(self, self_private_request, e):
        if isinstance(e, BadPassword):
            self.logger_.exception(e)
            self.change_proxy()
            if self_private_request.relogin_attempt > 0:
                self_private_request.freeze(str(e), days=7)
                raise ReloginAttemptExceeded(e)
            self.__client.set_settings(self.rebuild_client_settings())
            self.save_settings()
        elif isinstance(e, LoginRequired):
            self.logger_.error(f"| LOGIN REQUIRED: {e}")
            self.__client.relogin()
            self.save_settings()
        elif isinstance(e, ChallengeRequired):
            api_path = self_private_request.last_json.get("challenge", {}).get("api_path")
            if api_path == "/challenge/":
                self.change_proxy()
                self.__client.set_settings(self.rebuild_client_settings())
                self.save_settings()
                self_private_request.logger()
            else:
                try:
                    self_private_request.challenge_resolve(self_private_request.last_json)
                except ChallengeRequired as e:
                    client.freeze("Manual Challenge Required", days=2)
                    raise e
                except (
                        ChallengeRequired,
                        SelectContactPointRecoveryForm,
                        RecaptchaChallengeForm,
                ) as e:
                    client.freeze(str(e), days=4)
                    raise e
                client.update_client_settings(client.get_settings())
            return True
        elif isinstance(e, FeedbackRequired):
            message = client.last_json["feedback_message"]
            if "This action was blocked. Please try again later" in message:
                client.freeze(message, hours=12)
                # client.settings = self.rebuild_client_settings()
                # return self.update_client_settings(client.get_settings())
            elif "We restrict certain activity to protect our community" in message:
                # 6 hours is not enough
                client.freeze(message, hours=12)
            elif "Your account has been temporarily blocked" in message:
                """
                Based on previous use of this feature, your account has been temporarily
                blocked from taking this action.
                This block will expire on 2020-03-27.
                """
                client.freeze(message)
        elif isinstance(e, PleaseWaitFewMinutes):
            client.freeze(str(e), hours=1)
        raise e
