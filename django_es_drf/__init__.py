from .document_registry import registry
from .document import DjangoDocument
from .drf.viewsets import ESViewSet
from .drf.aggs import AggBase, BucketAgg, TranslatedBucketAgg, NestedAgg, SeparatorAgg
from .drf.serializers import ESDocumentSerializer
from .drf.pagination import ESPagination, ESPage, ESPaginator
from .drf.backends.source import DynamicSourceBackend
from .drf.backends.filters import (
    ESAggsFilterBackend,
    QueryFilterBackend,
    BaseESFilterBackend,
)
from .drf.renderers import ESRenderer
from .indexer import bulk_es, disabled_es
from .json import ESEncoderClass, to_plain_json, es_dump


def g(obj, key):
    if key in obj:
        return obj[key]
    return None


def remove_nulls(d):
    for k, v in list(d.items()):
        if v is None:
            del d[k]
    return d
