from typing import TypedDict


class VehicleAttribute(TypedDict):
    value: str
    type: str


def get_attribute_value(attribute: VehicleAttribute):
    if not attribute:
        return None
    value = attribute.get("value")
    dtype = attribute.get("type")
    if not dtype or not value:
        return value
    if dtype == "number":
        return str(value).strip()
    elif dtype == "string":
        if value.strip() in ("true", "false"):
            return {"true": True, "false": False}.get(value.strip())
    return value.strip()
