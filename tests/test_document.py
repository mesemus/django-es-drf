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
        doc = SchoolDocument(name="test", address="blah")
        doc.save()

        s = doc.to_django()
        s_id = s.id

        assert doc.name == s.name
        assert doc.address == s.address

        doc.delete()

        with self.assertRaises(NotFoundError):
            SchoolDocument.get(s_id)

        with self.assertRaises(School.DoesNotExist):
            School.objects.get(pk=s_id)
