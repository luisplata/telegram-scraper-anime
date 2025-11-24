import requests

WEBHOOK_URL = "https://backend.animebell.peryloth.com/api/webhook/send-anime-full"
WEBHOOK_TOKEN = "AnimeBell@1"

def send_to_webhook(data: list) -> None:
    headers = {
        "X-Webhook-Token": WEBHOOK_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post(WEBHOOK_URL, json=data, headers=headers)
    response.raise_for_status()
