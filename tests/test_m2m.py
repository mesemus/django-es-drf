from django.test import TestCase

from django_es_drf.indexer import bulk_es
from tests.app.models import SchoolWithM2MDocument, Person, \
    SchoolWithM2M


class M2MTestCase(TestCase):
    def setUp(self) -> None:
        try:
            SchoolWithM2MDocument._index.delete()
        except:
            pass
        SchoolWithM2MDocument._index.create()

    def test_create_update_delete(self):
        p1 = Person.objects.create(name="Kate")
        p2 = Person.objects.create(name="Jim")
        s = SchoolWithM2M.objects.create(name="test")
        with bulk_es():
            s.people.add(p1, p2)
        doc = SchoolWithM2MDocument.get(id=s.id)
        print(doc.to_dict())
        self.assertDictEqual(doc.to_dict(), {
            'id': 1,
            'name': 'test',
            'people': [
                {'id': 1, 'name': 'Kate'},
                {'id': 2, 'name': 'Jim'}
            ]
        })
