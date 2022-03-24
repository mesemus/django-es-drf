import re

from elasticsearch_dsl import Search
from rest_framework.filters import BaseFilterBackend


class DynamicSourceBackend(BaseFilterBackend):
    """Dynamic source backend."""

    def filter_queryset(self, request, queryset, view):
        if isinstance(queryset, Search) and hasattr(view, "source"):
            include = request.GET.get("include", None)
            exclude = request.GET.get("exclude", None)

            declared_source = view.source
            if not isinstance(declared_source, dict):
                declared_source = {"includes": declared_source, "excludes": []}
            if exclude:
                declared_source["excludes"].extend(
                    x.strip() for x in exclude.split(",")
                )
            if include:
                includes = [x.strip() for x in include.split(",")]
                ok_includes = []
                declared = "|".join(
                    self.to_regex(x) for x in declared_source["includes"]
                )
                for include in includes:
                    if re.match(declared, include):
                        ok_includes.append(include)
                declared_source["includes"] = ok_includes
            return queryset.source(declared_source)

        return queryset

    def to_regex(self, pathspec):
        pathspec = pathspec.replace(".", r"\.")
        pathspec = pathspec.replace("*", r".*")
        return f"^{pathspec}$"
