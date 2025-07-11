

class Source:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url
        }


class Episode:
    def __init__(self, title: str, number: int, link: str = "", message_id: int = 0):
        self.title = title
        self.number = number
        self.link = link
        self.source: list[Source] = []
        self.message_id: int = message_id
        self.path: str = ""

    def add_source(self, source: Source):
        self.source.append(source)

    def to_dict(self):
        return {
            "title": self.title,
            "number": self.number,
            "link": self.link,
            "source": [s.to_dict() for s in self.source],
            "message_id": self.message_id
        }


class Anime:
    def __init__(self, name: list[str], slug: str, description: str, image: str):
        self.name = name
        self.slug = slug
        self.description = description
        self.image = image
        self.caps: list[Episode] = []
        self.alterNames = []
        self.genres = []

    def add_cap(self, cap: Episode):
        self.caps.append(cap)

    def to_dict(self):
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "image": self.image,
            "caps": [cap.to_dict() for cap in self.caps],
            "alterNames": self.alterNames,
            "genres": self.genres
        }