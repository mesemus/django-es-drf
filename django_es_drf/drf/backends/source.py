import copy

from elasticsearch_dsl import Search
from rest_framework.filters import BaseFilterBackend


class DynamicSourceBackend(BaseFilterBackend):
    """Dynamic source backend."""

    def filter_queryset(self, request, queryset, view):
        if not isinstance(queryset, Search):
            return queryset

        if hasattr(view, "is_dynamic_source_filtering_enabled"):
            if not view.is_dynamic_source_filtering_enabled(request):
                return queryset

        # only in listing urls
        lookup_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        if lookup_url_kwarg in view.kwargs:
            return queryset

        include = request.GET.get("_include", None)
        exclude = request.GET.get("_exclude", None)

        if hasattr(view, "source") and view.source:
            if not isinstance(view.source, dict):
                declared_source = {"includes": [*view.source], "excludes": []}
            else:
                declared_source = {
                    "includes": [],
                    "excludes": [],
                    **copy.deepcopy(view.source),
                }
        else:
            declared_source = {"includes": [], "excludes": []}

        if exclude:
            declared_source["excludes"].extend(x.strip() for x in exclude.split(","))

        if include:
            declared_source["includes"].extend(x.strip() for x in include.split(","))
        if not declared_source["includes"]:
            declared_source["includes"] = ["*"]

        return queryset.source(declared_source)

    def to_regex(self, pathspec):
        pathspec = pathspec.replace(".", r"\.")
        pathspec = pathspec.replace("*", r".*")
        return f"^{pathspec}$"
