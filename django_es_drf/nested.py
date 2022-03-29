import elasticsearch_dsl as e
from rest_framework import serializers


def object_builder(fld_name, fld, ctx, **kwargs):
    new_mapping = _build_mapping(fld_name, fld, ctx)
    return e.Object(properties=new_mapping, **kwargs)


def nested_builder(fld_name, fld, ctx, **kwargs):
    new_mapping = _build_mapping(fld_name, fld, ctx)
    return e.Nested(properties=new_mapping, **kwargs)


def _build_mapping(fld_name, fld, ctx):
    from django_es_drf.document_registry import RegistrationContext
    from django_es_drf.document_generator import generate_mapping

    nested_prefix = ctx.prefix + fld_name + "."
    nested_context = RegistrationContext(**{**ctx._asdict(), "prefix": nested_prefix})
    # TODO: mozny merge, pokud uz nested/object field existuje na dokumentu
    new_mapping = generate_mapping(
        nested_prefix, nested_context, {}, ctx.included, ctx.excluded, fld
    )
    return new_mapping


def serializer_object_builder(fld_name, fld, ctx, **kwargs):
    from django_es_drf.serializer_generator import generate_mapping
    from django_es_drf.document_registry import RegistrationContext

    nested_prefix = ctx.prefix + fld_name + "."
    nested_context = RegistrationContext(**{**ctx._asdict(), "prefix": nested_prefix})
    new_mapping = generate_mapping(
        nested_prefix, nested_context, None, ctx.included, ctx.excluded, fld._mapping
    )
    return type(f"{fld_name}Serializer", (serializers.Serializer,), new_mapping)(
        required=False
    )
