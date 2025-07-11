# Clase base para handles de canal
class ChannelHandle:
    key = None
    channel_id = None

    def __init__(self, entity):
        self.entity = entity

    def parse_message(self, message):
        return message.text