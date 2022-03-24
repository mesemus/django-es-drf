import math
from collections import OrderedDict

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ESPage(Page):
    pass


class ESPaginator(Paginator):
    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger(_("That page number is not an integer"))
        if number < 1:
            raise EmptyPage(_("That page number is less than 1"))
        return number

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        self.object_list = self.object_list[bottom:top].execute()
        self.total = self.object_list.hits.total.value
        return ESPage(self.object_list, number, self)

    @property
    def num_pages(self):
        return math.ceil(self.total / self.per_page)

    @property
    def aggs(self):
        if hasattr(self, "_aggs") and self._aggs:
            return self._aggs
        return self.object_list.aggs

    @aggs.setter
    def aggs(self, value):
        self._aggs = value


class ESPagination(PageNumberPagination):
    django_paginator_class = ESPaginator
    page_size_query_param = "size"
    page_size = 10

    def get_paginated_response(self, data):
        for backend in self.view.filter_backends:
            if hasattr(backend, "process_result"):
                backend().process_result(
                    self.request, self, self.page.paginator, self.view
                )

        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.total),
                    ("page", self.page.number),
                    ("size", self.page.paginator.per_page),
                    ("pages", self.page.paginator.num_pages),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("hits", data),
                    ("aggs", self.page.paginator.aggs),
                ]
            )
        )

    def paginate_queryset(self, queryset, request, view=None):
        self.view = view
        return super().paginate_queryset(queryset, request, view)
