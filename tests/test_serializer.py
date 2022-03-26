from django.test import TestCase

from tests.app.models import (
    SchoolWithSerializer,
    SchoolWithSerializerDocument,
    SchoolForSerializerGeneratorDocument,
)


class MapppingTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolForSerializerGeneratorDocument._index.delete()
        except:
            pass
        SchoolForSerializerGeneratorDocument._index.create()

    def test_serializer_from_django_to_doc(self):
        s = SchoolWithSerializer.objects.create(name="test", address="blah")
        doc = SchoolWithSerializerDocument.from_django(s)
        assert doc.name_with_address == "test, blah"

    def test_generate_serializer_from_doc(self):
        doc = SchoolForSerializerGeneratorDocument(name="test", address="blah")
        doc.save()
