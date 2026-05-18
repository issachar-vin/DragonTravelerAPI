from bson import ObjectId


def serialize_value(value):
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, dict):
        return serialize_nested(value)
    elif isinstance(value, list):
        return [serialize_value(item) for item in value]
    return value


def serialize_nested(d: dict) -> dict:
    return {k: serialize_value(v) for k, v in d.items()}


def serialize_doc(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, list):
            doc[k] = [serialize_value(item) for item in v]
        elif isinstance(v, dict):
            doc[k] = serialize_nested(v)
    return doc
