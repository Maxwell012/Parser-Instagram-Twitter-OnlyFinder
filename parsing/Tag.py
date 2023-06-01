import requests
from bs4 import BeautifulSoup

from common_variables import database


class Tag:
    def __init__(self):
        self.page = 0

    @staticmethod
    def check_tags(tags: list) -> list:
        """Remove tags that already is in DataBase"""

        database.execute("SELECT tag FROM old_tag")
        old_tags = set([row[0] for row in database.fetchall()])
        return list(set(tags).difference(old_tags))

    def get_new_tags(self) -> list:
        """Tags from https://www.10-letter-words.com/"""

        url = f'https://www.10-letter-words.com/?page={self.page}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        list_ = soup.find('ul', class_='list-unstyled')
        words = [word['href'].replace("./word-", "") for word in list_.find_all('a')]
        self.page += 1
        return words

    def generate_tags(self) -> list:
        while True:
            new_tags = self.get_new_tags()
            unique_tags = self.check_tags(new_tags)
            for tag in unique_tags:
                yield tag

    @staticmethod
    def insert_tag(tag, count_models):
        database.execute(f"INSERT INTO old_tag VALUES('{tag}', {count_models})")
        database.commit()
