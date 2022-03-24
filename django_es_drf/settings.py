from django.conf import settings
from rest_framework import fields, serializers
import elasticsearch_dsl as e

from django_es_drf.nested import object_builder


def get(key, default):
    return getattr(settings, key, default)


DJANGO_ES_DEFAULT_FIELD_MAPPING = get(
    "DJANGO_ES_DEFAULT_FIELD_MAPPING",
    {
        fields.CharField: lambda fld_name, fld, ctx, **kwargs: e.Keyword(**kwargs),
        fields.IntegerField: lambda fld_name, fld, ctx, **kwargs: e.Integer(**kwargs),
        fields.FloatField: lambda fld_name, fld, ctx, **kwargs: e.Float(**kwargs),
        fields.DateTimeField: lambda fld_name, fld, ctx, **kwargs: e.Date(**kwargs),
        fields.DateField: lambda fld_name, fld, ctx, **kwargs: e.Date(**kwargs),
        serializers.Serializer: object_builder,
    },
)
