from collections import defaultdict

from elasticsearch_dsl import Search
from rest_framework.filters import BaseFilterBackend


class ESFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if not isinstance(queryset, Search):
            return queryset
        for es_filter in view.es_filter_backends:
            queryset = es_filter().filter_queryset(request, queryset, view)
        return queryset


class BaseESFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset

    def process_result(self, request, pagination, paginator, view):
        pass


class ESAggsFilterBackend(BaseESFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for agg in view.aggs:
            agg = agg.top
            agg.apply(queryset.aggs)
        f = request.GET.get("f", None)
        if f:
            f = self.parse_facets(f)
            for agg in view.aggs:
                agg = agg.top
                for query in agg.filter(f):
                    queryset = queryset.filter(query)
        return queryset

    def parse_facets(self, facets):
        facets = [
            x.replace("%3A", ":").replace("%3a", ":").replace("%25", "%")
            for x in facets.split(":")
        ]
        ret = defaultdict(list)
        for k, v in zip(facets[0::2], facets[1::2]):
            ret[k].append(v)
        return ret

    def process_result(self, request, pagination, paginator, view):
        agg_result = paginator.aggs.to_dict()
        ret_aggs = []
        for agg in view.aggs:
            agg = agg.top
            r = agg.process_result(agg_result)
            if r:
                ret_aggs.append(r)
        paginator.aggs = ret_aggs


class QueryFilterBackend(BaseESFilterBackend):
    def filter_queryset(self, request, queryset, view):
        q = request.GET.get("q")
        if not q:
            return queryset
        filter_view_method = f"filter_es_{view.action.lower()}"
        if hasattr(view, filter_view_method):
            queryset = getattr(view, filter_view_method)(queryset, q)
        else:
            parser_id = request.GET.get("parser", "simple")
            parser = view.query_parsers.get(parser_id) or view.query_parsers["simple"]
            queryset = parser(request, queryset, view, q)
        return queryset
