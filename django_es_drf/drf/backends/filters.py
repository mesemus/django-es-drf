from collections import defaultdict

from elasticsearch_dsl import Search
from rest_framework.filters import BaseFilterBackend


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
        if hasattr(view, "parse_facet_query"):
            f = view.parse_facet_query(request)
        else:
            f = request.GET.get("f", None)
            if f:
                f = self.parse_facets(f)
        if f:
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
        interpreter = self._get_query_interpreter(view, request)
        if interpreter:
            queryset = interpreter(request, queryset, view, q)
        else:
            return queryset.filter("match_none")  # match none on invalid parser
        return queryset

    @staticmethod
    def _get_query_interpreter(view, request):
        parser_id = request.GET.get("parser", None)
        if not parser_id:
            return view.default_query_interpreter
        return view.query_interpreters.get(parser_id)
