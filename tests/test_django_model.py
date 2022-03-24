from django.test import TestCase
from elasticsearch import NotFoundError

from tests.app.models import School, SchoolDocument


class DjangoModelTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolDocument._index.delete()
        except:
            pass
        SchoolDocument._index.create()

    def test_create_update_delete(self):
        s = School.objects.create(name="test", address="blah")
        s_id = s.id
        doc = SchoolDocument.get(id=s_id)
        assert doc.name == s.name
        assert doc.address == s.address

        s.delete()
        with self.assertRaises(NotFoundError):
            SchoolDocument.get(id=s_id)
