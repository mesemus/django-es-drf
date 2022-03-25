from django.test import TestCase

from tests.app.api import SchoolAPI
from tests.app.models import School, SchoolDocument


class DRFTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolDocument._index.delete()
        except:
            pass
        SchoolDocument._index.create()

    def tearDown(self) -> None:
        try:
            del SchoolAPI.source
        except:
            pass

    def test_es_listing(self):
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"id": 1, "name": "test", "address": "blah"}],
                "aggs": {},
            },
        )

    def test_aggs(self):
        School.objects.create(name="test 1", address="blah")
        School.objects.create(name="test 2", address="blah")

        resp = self.client.get("/schools2/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 2,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [
                    {"id": 1, "name": "test 1", "address": "blah"},
                    {"id": 2, "name": "test 2", "address": "blah"},
                ],
                "aggs": [
                    {
                        "code": "name",
                        "__missing__": 0,
                        "__count__": 2,
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": [
                            {"key": "test 1", "doc_count": 1},
                            {"key": "test 2", "doc_count": 1},
                        ],
                    },
                    {
                        "code": "address",
                        "__missing__": 0,
                        "__count__": 2,
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": [{"key": "blah", "doc_count": 2}],
                    },
                ],
            },
        )

    def test_source_filtering(self):
        SchoolAPI.source = ["name"]
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"name": "test"}],
                "aggs": {},
            },
        )

    def test_source_filtering_exclude(self):
        SchoolAPI.source = {"excludes": "address"}
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"id": 1, "name": "test"}],
                "aggs": {},
            },
        )

    def test_source_filtering_exclude_array(self):
        SchoolAPI.source = {"excludes": ["address"]}
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"id": 1, "name": "test"}],
                "aggs": {},
            },
        )

    def test_source_filtering_exclude_all(self):
        SchoolAPI.source = {"excludes": "*"}
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{}],
                "aggs": {},
            },
        )

    def test_source_filtering_query(self):
        SchoolAPI.source = ["address"]
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/?_include=name").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"name": "test", "address": "blah"}],
                "aggs": {},
            },
        )

    def test_source_filtering_query_exclude(self):
        SchoolAPI.source = ["name", "address"]
        School.objects.create(name="test", address="blah")
        resp = self.client.get("/schools/?_exclude=address").json()
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"name": "test"}],
                "aggs": {},
            },
        )

    def test_simple_query(self):
        School.objects.create(name="first", address="blah")
        School.objects.create(name="second", address="blah")

        resp = self.client.get("/schools/?q=first").json()
        print(resp)
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"address": "blah", "name": "first", "id": 1}],
                "aggs": {},
            },
        )

        resp = self.client.get("/schools/?q=blah").json()
        print(resp)
        self.assertDictEqual(
            resp,
            {
                "count": 2,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [
                    {"address": "blah", "name": "first", "id": 1},
                    {"address": "blah", "name": "second", "id": 2},
                ],
                "aggs": {},
            },
        )

    def test_luqum_query(self):
        School.objects.create(name="first", address="blah")
        School.objects.create(name="first", address="abc")
        School.objects.create(name="second", address="blah")

        resp = self.client.get(
            "/schools/?q=name:first AND address:blah&parser=luqum"
        ).json()
        print(resp)
        self.assertDictEqual(
            resp,
            {
                "count": 1,
                "page": 1,
                "size": 10,
                "pages": 1,
                "next": None,
                "previous": None,
                "hits": [{"address": "blah", "name": "first", "id": 1}],
                "aggs": {},
            },
        )

    def test_bad_query(self):
        School.objects.create(name="first", address="blah")
        School.objects.create(name="first", address="abc")
        School.objects.create(name="second", address="blah")

        resp = self.client.get(
            "/schools/?q=name:first AND address:blah&parser=bad"
        ).json()
        print(resp)
        self.assertDictEqual(
            resp,
            {
                "count": 0,
                "page": 1,
                "size": 10,
                "pages": 0,
                "next": None,
                "previous": None,
                "hits": [],
                "aggs": {},
            },
        )
