import requests
from flask import jsonify


class SendInBlueNotification:
    def __init__(self, api_url, api_key , email_from, name_from):
        self.send_in_blue_url = api_url
        self.email_from = email_from
        self.name_from = name_from
        self.send_in_blue_token = api_key

        self.headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'api-key': self.send_in_blue_token
        }

    def send(self, email_to, subject, message):
        data = {
            "sender": {
                "name": self.name_from,
                "email": self.email_from
            },
            "to":[{
                "email": email_to
            }],
            "htmlContent": message,
            "subject": subject,
            "replyTo":{
                "name": self.name_from,
                "email": self.email_from
            }
        }

        response = requests.request(
            method="POST",
            url=self.send_in_blue_url,
            headers=self.headers,
            json= data
        )

        return response