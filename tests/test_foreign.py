from django.test import TestCase

from tests.app.models import SchoolWithForeignDocument, SchoolWithForeign, City


class ForeignTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolWithForeignDocument._index.delete()
        except:
            pass
        SchoolWithForeignDocument._index.create()

    def test_create_update_delete(self):
        prague = City.objects.create(name="Prague")
        s = SchoolWithForeign.objects.create(name="test", city=prague)
        doc = SchoolWithForeignDocument.get(id=s.id)
        assert doc.name == s.name
        assert doc.city.id == prague.id
        assert doc.city.name == prague.name
