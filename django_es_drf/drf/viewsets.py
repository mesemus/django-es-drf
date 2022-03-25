from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from .backends.filters import ESAggsFilterBackend, QueryFilterBackend
from .backends.query_interpreters import (
    simple_query_interpreter,
    luqum_query_interpreter,
)
from .pagination import ESPagination
from .renderers import ESRenderer
from .serializers import CopyESSerializer
from .backends.source import DynamicSourceBackend


class ESViewSet(viewsets.ModelViewSet):
    pagination_class = ESPagination
    renderer_classes = [
        ESRenderer,
        BrowsableAPIRenderer,
    ]
    aggs = ()
    filter_backends = [DynamicSourceBackend, ESAggsFilterBackend, QueryFilterBackend]
    serializer_class = CopyESSerializer
    query_interpreters = {
        "simple": simple_query_interpreter,
        "luqum": luqum_query_interpreter,
    }
    # needed so that the function is not bound (otherwise it would get 'self' as the first parameter)
    default_query_interpreter = staticmethod(simple_query_interpreter)

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
