from django_es_drf.drf.aggs import BucketAgg
from django_es_drf.drf.viewsets import ESViewSet
from tests.app.models import SchoolDocument


class SchoolAPI(ESViewSet):
    document = SchoolDocument


class SchoolAPI2(ESViewSet):
    document = SchoolDocument
    aggs = [BucketAgg("name"), BucketAgg("address")]
