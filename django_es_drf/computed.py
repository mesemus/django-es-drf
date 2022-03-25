import inspect

from rest_framework import serializers


def serializer_method_field_builder(fld_name, fld, ctx, **kwargs):
    from django_es_drf.document_generator import generate_field_mapping

    method = getattr(ctx.serializer, f"get_{fld.field_name}")
    if hasattr(method, "output_type"):
        output = method.output_type
    else:
        output = serializers.CharField()
    if inspect.isclass(output):
        output = output()  # noqa
    return generate_field_mapping(fld_name, fld_name, output, ctx)
