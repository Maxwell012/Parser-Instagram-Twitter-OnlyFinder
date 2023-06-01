from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests import Session

from logger import logger
from .Parser import Parser

logger_ = logger("__onlyFinderRequest__")


class OnlyFinderRequest(Parser):

    def __init__(self):
        self.session = self.create_session()

    @staticmethod
    def create_session() -> Session:
        ua = UserAgent()
        headers = {
            "cookie": "_gcl_au=1.1.196950270.1680540558; cf_clearance=muDompcZwrMk36_.dATRWBr4PUgD4djGQwXWH578qhg-"
                      "1683068484-0-150; _gid=GA1.2.671531136.1683068486; _ga=GA1.1.1151142448.1680528381; "
                      "_ga_1PB9XEPVWM=GS1.1.1683155127.48.1.1683155128.59.0.0; connect.sid=s%3A-NaIeNcKStCsAPGTmmombTOMSC"
                      "MYo65-.sVaaL87JR1R0wLOgOMQRmFhtyNxuv9pyjV2ack9xFV8; _ga_G7953F1TMT=GS1.1.1683199106.1.1"
                      ".1683199995.0.0.0",
            "user-agent": ua.random
        }
        session = Session()
        session.headers = headers
        return session

    def rebuild_session(self):
        self.session = self.create_session()

    def get_models(self, tag) -> list or None:
        """Get models from OnlyFinder site by a tag"""

        print(f"TAG: {tag}")
        url = f"https://onlyfinder.com/{tag}/profiles"
        response = self.session.get(url)
        if response.status_code == 200:
            models = []
            try:
                soup = BeautifulSoup(response.text, "html.parser")
                for model in soup.select(".profile-container"):
                    instagram = ""
                    twitter = ""
                    for network in model.find_all('a', href=True):
                        if network.get("data-type") == "instagram":
                            instagram = self.get_username(network['href'], "instagram")
                        elif network.get("data-type") == "twitter":
                            twitter = self.get_username(network['href'], "twitter")

                    if instagram or twitter:
                        print(f"\t+ {instagram} | {twitter}")
                        models.append({"instagram": instagram if instagram else "",
                                       "twitter": twitter if twitter else ""})
            except Exception as ex:
                logger_.critical(f"ERROR IN DURING GETTING MODELS | {response.text} | {ex}", exc_info=True)
            finally:
                return models
        elif response.status_code == 502:
            logger_.error(f"STATUS CODE IS 502")
            self.session.close()
            self.timeout(60, 120)
            self.rebuild_session()
            self.get_models(tag)
        elif response.status_code == 403:
            logger_.error(f"STATUS CODE IS 403")
            self.session.close()
            self.timeout(60, 120)
            self.rebuild_session()
            self.get_models(tag)
        else:
            logger_.critical(f"STATUS CODE IS NOT 200 | {response.status_code} | {response.text}")
            self.session.close()
            self.timeout(60, 120)
            self.rebuild_session()
