from luqum.elasticsearch import SchemaAnalyzer, ElasticsearchQueryBuilder
from luqum.parser import parser
from luqum.utils import UnknownOperationResolver


def simple_query_interpreter(request, queryset, view, q):
    # simple query
    filter_transform_method = f"filter_es_transform_query_{view.action.lower()}"
    if hasattr(view, filter_transform_method):
        q = getattr(view, filter_transform_method)(q)
    return queryset.query("multi_match", query=q, fields=["*"])


def luqum_query_interpreter(request, queryset, view, q):
    # luqum query
    return apply_luqum(queryset, q, view.document)


def apply_luqum(queryset, query, document):
    tree = parser.parse(query)
    resolver = UnknownOperationResolver()
    tree = resolver(tree)
    analyzer = SchemaAnalyzer(document._index.to_dict())
    message_es_builder = ElasticsearchQueryBuilder(**analyzer.query_builder_options())
    return queryset.query(message_es_builder(tree))
