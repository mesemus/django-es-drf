import json
from json import JSONEncoder
from elasticsearch_dsl import Document, AttrList, AttrDict
from elasticsearch_dsl.response import AggResponse


def to_plain_json(doc):
    return json.loads(es_dump(doc.to_dict()))


class ESEncoderClass(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Document):
            return obj.to_dict(skip_empty=False)
        if isinstance(obj, AttrList):
            return obj._l_
        if isinstance(obj, AttrDict):
            return obj._d_
        if isinstance(obj, AggResponse):
            return obj.to_dict()
        return super().default(obj)


def es_dump(obj, **kwargs):
    return json.dumps(obj, cls=ESEncoderClass, **kwargs)
