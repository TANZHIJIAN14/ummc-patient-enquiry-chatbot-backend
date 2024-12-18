import base64

from bson import ObjectId, Binary


def serialize_mongo_document(doc):
    serialized_doc = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            serialized_doc[key] = str(value)
        elif isinstance(value, (Binary, bytes)):
            serialized_doc[key] = base64.b64encode(value).decode('utf-8')
        else:
            serialized_doc[key] = value
    return serialized_doc