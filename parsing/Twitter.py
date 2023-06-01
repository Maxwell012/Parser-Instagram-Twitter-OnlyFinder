from snscrape.modules.twitter import TwitterUserScraper

from logger import logger
from parsing.Parser import Parser

logger_ = logger("__twitter__")


class Twitter(Parser):
    def get_user_info(self, username) -> list:
        try:
            crawler = TwitterUserScraper(username)
            data = crawler._get_entity()
            if data:
                location = self.remove_formatting(data.location) if data.location else None
                email = self.find_email(data.rawDescription)
                phone = self.find_phone_number(data.rawDescription)
                result = [username, f"https://twitter.com/{username}/", location, phone, email]
            else:
                result = [username, f"https://twitter.com/{username}/", None, None, None]
            return result
        except Exception as ex:
            logger_.critical(f"| UNKNOW ERROR - {ex}", exc_info=True)
            return [username, f"https://twitter.com/{username}/", None, None, None]
