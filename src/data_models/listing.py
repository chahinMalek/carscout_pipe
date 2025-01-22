from pydantic import BaseModel


class VehicleListing(BaseModel):
    title: str
    price: str
    url: str
    article_id: str
