from django.http import Http404
from elasticsearch_dsl import Q
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from .backends.filters import ESFilterBackend, ESAggsFilterBackend, QueryFilterBackend
from .backends.parsers import simple_query_parser, luqum_query_parser
from .pagination import ESPagination
from .renderers import ESRenderer
from .serializers import CopyESSerializer


class ESViewSet(viewsets.ModelViewSet):
    pagination_class = ESPagination
    renderer_classes = [
        ESRenderer,
        BrowsableAPIRenderer,
    ]
    aggs = ()
    filter_backends = [ESAggsFilterBackend, QueryFilterBackend]
    serializer_class = CopyESSerializer
    query_parsers = {"simple": simple_query_parser, "luqum": luqum_query_parser}

    @property
    def document(self):
        raise AttributeError(
            f"Please specify document=<document class> on this viewset ({type(self)})"
        )

    def get_queryset(self):
        return self.document.search()

    # @property
    # def lookup_field(self):
    #     if self.action in self.es_actions:
    #         return self.es_lookup_field
    #     return self.django_lookup_field
    #
    # def get_object(self):
    #     if self.action not in self.es_actions:
    #         return super().get_object()
    #
    #     queryset = self.filter_queryset(self.get_queryset())
    #     lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
    #     filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
    #     data = list(queryset.filter(Q('term', **filter_kwargs))[:1])
    #     if not data:
    #         raise Http404()
    #     obj = data[0]
    #
    #     self.check_object_permissions(self.request, obj)
    #
    #     return obj
    #
    # def filter_queryset(self, queryset):
    #     return super().filter_queryset(queryset)
    #
    # def get_list_queryset(self):
    #     return self.queryset.model.DocumentMeta.document.search()
    #
    # def get_detail_queryset(self):
    #     return super().get_queryset()
    #
    # def get_serializer_class(self):
    #     if self.action in self.es_actions:
    #         return self.es_serializer
    #     return super().get_serializer_class()
