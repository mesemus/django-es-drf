from django.test import TestCase

from tests.app.models import (
    SchoolWithSerializer,
    SchoolWithSerializerDocument,
)


class MapppingTestCase(TestCase):
    def test_serializer_from_django_to_doc(self):
        s = SchoolWithSerializer.objects.create(name="test", address="blah")
        doc = SchoolWithSerializerDocument.from_django(s)
        assert doc.name_with_address == "test, blah"
