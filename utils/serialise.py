from bson import ObjectId


def doc_to_dict(doc):

    if doc is None:
        return None

    result = {}

    for k, v in doc.items():

        if k == "_id":
            result["id"] = str(v)

        elif isinstance(v, ObjectId):
            result[k] = str(v)

        elif isinstance(v, list):

            result[k] = [
                doc_to_dict(i) if isinstance(i, dict) else i    
                for i in v
            ]

        elif isinstance(v, dict):
            result[k] = doc_to_dict(v)

        elif hasattr(v, "isoformat"):
            result[k] = v.isoformat()

        else:
            result[k] = v

    return result