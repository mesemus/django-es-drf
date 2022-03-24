from django.test import TestCase

from tests.app.models import School, SchoolDocument


class DRFTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolDocument._index.delete()
        except:
            pass
        SchoolDocument._index.create()

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
