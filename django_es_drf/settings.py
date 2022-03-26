from django.conf import settings
from rest_framework import fields, serializers
import elasticsearch_dsl as e

from django_es_drf.nested import object_builder, serializer_object_builder


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
        fields.BooleanField: lambda fld_name, fld, ctx, **kwargs: e.Boolean(**kwargs),
        fields.NullBooleanField: lambda fld_name, fld, ctx, **kwargs: e.Boolean(
            **kwargs
        ),
        serializers.Serializer: object_builder,
        serializers.SerializerMethodField: lambda fld_name, fld, ctx, **kwargs: e.Keyword(
            **kwargs
        ),
    },
)


ES_DRF_DEFAULT_FIELD_MAPPING = get(
    "ES_DRF_DEFAULT_FIELD_MAPPING",
    {
        e.Keyword: lambda fld_name, fld, ctx, **kwargs: fields.CharField(
            **{"required": False, **kwargs}
        ),
        e.Integer: lambda fld_name, fld, ctx, **kwargs: fields.IntegerField(
            **{"required": False, **kwargs}
        ),
        e.Float: lambda fld_name, fld, ctx, **kwargs: fields.FloatField(
            **{"required": False, **kwargs}
        ),
        e.Date: lambda fld_name, fld, ctx, **kwargs: fields.DateTimeField(
            **{"required": False, **kwargs}
        ),
        e.Boolean: lambda fld_name, fld, ctx, **kwargs: fields.BooleanField(
            **{"required": False, **kwargs}
        ),
        e.Object: serializer_object_builder,
    },
)
