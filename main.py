import json
import os
import time

from common_variables import database
from logger import logger
from parsing.Instagram import Instagram
from parsing.Instantly import Instantly
from parsing.OnlyFinderRequest import OnlyFinderRequest
from parsing.Parser import Parser
from parsing.Tag import Tag
from parsing.Twitter import Twitter

# Create logger
logger_main = logger("__main__")

# Create all classes for parsing
only_finder_request = OnlyFinderRequest()
twitter = Twitter()
parser = Parser()
tag = Tag()
instantly = Instantly()
instagrams = []
print(f"ACCOUNTS:\n")
for index, filename in enumerate(os.listdir("parsing/settings")[:20]):
    with open("parsing/settings/" + filename + "/settings.json") as file:
        settings = json.load(file)
    with open("parsing/settings/" + filename + "/data.json") as file:
        data = json.load(file)

    username = data['instagram']['username']
    password = data['instagram']['password']
    mail_username = data['mail']['username']
    mail_password = data['mail']['password']
    proxy = data["proxy"]

    if "mail.ru" in mail_username:
        host = "imap.mail.ru"
    else:
        host = "imap.firstmail.ltd"

    print(f"{index+1}\t{username} | {password} | {mail_username} | {mail_password} | {proxy}")

    instagrams.append(Instagram(username=username,
                               password=password,
                               mail_username=mail_username,
                               mail_password=mail_password,
                               host=host,
                               settings=settings,
                               proxy=proxy))


def benchmark(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"Execution time for ({func.__name__}): {time.time() - start_time}")
        return result

    return wrapper


@benchmark
def main():
    count_of_all_new_models = 0
    with open("test_words.txt") as f:
        tags = [tag_.strip() for tag_ in f.readlines()]

    try:
        for tag_ in tag.check_tags(tags):
            tag_ = tag_.strip()
            count_of_new_models = job_tag(tag_)
            if count_of_new_models:
                tag.insert_tag(tag_, count_of_new_models)

                print(f"\tCount of new models that were added in during one tag ({tag_}): {count_of_new_models}\n")
                count_of_all_new_models += count_of_new_models
                instantly.upload_data()
    finally:
        print(f"New models were parsed: {count_of_all_new_models}")


@benchmark
def job_tag(tag_) -> int | None:
    count_of_new_models = 0
    models_networks = only_finder_request.get_models(tag_)
    if models_networks:
        print("Count of values: " + str(len(models_networks)))
        models_networks = remove_duplicates(models_networks)
        print("Count of unique values: " + str(len(models_networks)))

        data_instagram, data_twitter = manage_parsing(models_networks)
        insert_data(models_networks, data_instagram, data_twitter)
        print(f"\tCount of new models: {len(models_networks)}\n"
              f"\tNew models were added\n")

        number_of_models = len(models_networks)
        count_of_new_models += number_of_models
        return count_of_new_models


def manage_parsing(models_networks) -> [list, list]:
    data_twitter = []
    data_instagram = []
    start_delay = 0
    for index, social_networks in enumerate(models_networks):
        print(f"{index} - {social_networks['instagram']} | {social_networks['twitter']}")
        if social_networks["instagram"]:
            if time.time() - start_delay < 10:
                time.sleep(40)
            result = None
            while not result:
                instagram = get_instagram()
                result = instagram.get_user_info(social_networks["instagram"])

            print(f"INSTAGRAM: {result}")
            data_instagram.append(result)
            start_delay = time.time()
            # parser.timeout(5, 15)
        if social_networks["twitter"]:
            result = twitter.get_user_info(social_networks["twitter"])
            print(f"TWITTER: {result}")
            data_twitter.append(result)
    return data_instagram, data_twitter


def get_instagram():
    time_available = 10000
    instagram = None
    for instagram in instagrams:
        if instagram.get_time_available() < time_available:
            time_available = instagram.get_time_available()
    return instagram


def insert_data(models_network, data_instagram, data_twitter)   :
    database.executemany("INSERT INTO twitter VALUES(?, ?, ?, ?, ?)", data_twitter)
    database.executemany("INSERT INTO instagram VALUES(?, ?, ?, ?, ?, ?, ?)", data_instagram)
    data_ = [(d['instagram'] if d["instagram"] else None, d['twitter'] if d["twitter"] else None)
             for d in models_network]
    database.executemany(f"INSERT INTO model (instagram, twitter) VALUES (?, ?)", data_)
    database.commit()


def remove_duplicates(models_networks) -> list:
    """Remove duplicate models + remove models that have already been added to the database"""

    models_networks = [dict(i) for i in set([tuple(j.items()) for j in models_networks])]
    database.execute("""SELECT json('{ "instagram": "' || coalesce(instagram, '') || '", 
        "twitter": "' || coalesce(twitter, '') || '" }') AS data FROM model""")
    old_models_networks = [json.loads(row[0]) for row in database.fetchall()]

    for dict_ in old_models_networks:
        try:
            models_networks.remove(dict_)
        except ValueError:
            pass
    return models_networks


if __name__ == '__main__':
    main()
