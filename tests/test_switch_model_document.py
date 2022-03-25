from django.test import TestCase
from elasticsearch import NotFoundError

from tests.app.models import School, SchoolDocument


class SwitchModelDocumentTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolDocument._index.delete()
        except:
            pass
        SchoolDocument._index.create()

    def test_switch(self):
        School.objects.create(name="test", address="blah")

        django_school = School.objects.get(pk=1)
        document_school = SchoolDocument.from_django(django_school)
        assert document_school.meta.id == 1
        django_again = document_school.to_django()

        # they are not the same instances though
        assert django_school is not django_again
