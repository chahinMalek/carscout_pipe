from dataclasses import dataclass


@dataclass
class Brand:
    id: str
    name: str
    slug: str

    def __post_init__(self):
        self.id = self.id.strip()
        self.name = self.name.strip()
        self.slug = self.slug.strip()
