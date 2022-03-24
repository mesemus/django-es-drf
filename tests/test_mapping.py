from django.test import TestCase
import elasticsearch_dsl as e
from tests.app.models import SchoolWithNameAsTextDocument


class MapppingTestCase(TestCase):
    def test_model_with_text(self):
        self.assertIsInstance(
            SchoolWithNameAsTextDocument._doc_type.mapping["name"], e.Text
        )
