import more_itertools
from requests import Session
from requests.exceptions import JSONDecodeError

from common_variables import database
from config import API_KEY_INSTANTLY, CAMPAIGN_ID
from logger import logger

logger_ = logger("__instantly__")


class Instantly:
    def __init__(self):
        self.api_key = API_KEY_INSTANTLY
        self.campaign_id = CAMPAIGN_ID
        self.session = Session()
        self.last_id = 0
        self.upload_data()

    def upload_data(self):
        """ Upload a data to a campaign in Instantly.ai """

        data = self.get_good_models()
        if len(data) > 10:
            data = self.change_format_data(data)
            for chunk in more_itertools.chunked(data, 500):
                payload = {
                    "api_key": self.api_key,
                    "campaign_id": self.campaign_id,
                    "skip_if_in_workspace": False,
                    "leads": chunk
                }
                url = "https://api.instantly.ai/api/v1/lead/add"
                response = self.session.post(url, json=payload)
                try:
                    result = response.json()
                except JSONDecodeError:
                    logger_.error(f" | JSONDecodeError | {response.text}", exc_info=True)
                    return

                if 'status' in result:
                    if result['status'] == 'success':
                        print(f"Data is added. Result:")
                        for key, value in result.items():
                            if key == 'Data':
                                continue
                            print(f"\t{key}: {value}")
                        self.last_id = self.get_last_id()
                    else:
                        print(f"The status isn`t success: {result}")
                else:
                    print("CRITICAL ERROR IN INSTANTLY")
                    logger_.critical(f"\nResponse: {result}\n")
            print(f"LAST ID: {self.last_id}\n")
        else:
            print("There isn`t new models")

    @staticmethod
    def change_format_data(list_models) -> list:
        new_list = []
        for model in list_models:
            new_list.append({
                "email": model.pop("email"),
                "first_name": model.pop("first_name"),
                "phone": model.pop("phone"),
                "custom_variables": model
            })

        return new_list

    def get_good_models(self) -> list:
        query = """
            SELECT i.first_name, i.username, i.full_name, i.url AS instagram_url, i.followers,
            t.url AS twitter_url, t.country, i.phone, COALESCE(i.email, t.email) AS email
            FROM model m
            LEFT JOIN instagram i ON m.instagram = i.username
            LEFT JOIN twitter t ON m.twitter = t.username
            WHERE (i.email IS NOT NULL OR t.email IS NOT NULL)
        """ + f"AND m.id > {self.last_id};"
        database.execute(query)
        rows = database.fetchall()
        columns = [description[0] for description in database.cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        return result

    @staticmethod
    def get_last_id() -> int:
        query = "SELECT id FROM model ORDER BY id DESC LIMIT 1"
        database.execute(query)
        last_id = database.fetchall()[0][0]
        return last_id
