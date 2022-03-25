from django.test import TestCase
from elasticsearch import NotFoundError

from tests.app.models import School, SchoolDocument


class DocumentTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolDocument._index.delete()
        except:
            pass
        SchoolDocument._index.create()

    def test_create_update_delete(self):
        # create and check django
        doc = SchoolDocument(name="test", address="blah")
        doc.save()

        s = doc.to_django()
        s_id = s.id

        assert doc.name == s.name
        assert doc.address == s.address

        # search

        found = list(SchoolDocument.search().filter("term", name="test"))
        self.assertEqual(len(found), 1)

        found = list(SchoolDocument.search().filter("term", name="test not found"))
        self.assertEqual(len(found), 0)

        # update
        doc.address = "modified"
        doc.save()

        obj = School.objects.get(pk=doc.meta.id)
        assert obj.address == doc.address

        found = list(SchoolDocument.search().filter("term", name="test"))
        assert found[0].address == obj.address

        # delete

        doc.delete()

        with self.assertRaises(NotFoundError):
            SchoolDocument.get(s_id)

        with self.assertRaises(School.DoesNotExist):
            School.objects.get(pk=s_id)
