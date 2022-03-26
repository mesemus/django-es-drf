import inspect
from typing import Type, List, Dict, Callable, Union

import elasticsearch_dsl as e
from django.db import models
from rest_framework import serializers

from django_es_drf.document_registry import RegistrationContext


def generate_extra_serializer_fields(
    document: Type[e.Document],
    model: Type[models.Model],
    serializer: Type[serializers.ModelSerializer],
    serializer_mapping: Union[
        Dict[
            Type[e.Field],
            Union[Callable[[e.Field], RegistrationContext], Type[serializers.Field]],
        ],
        Dict[
            str,
            Union[Callable[[e.Field], RegistrationContext], Type[serializers.Field]],
        ],
    ],
    included: List[str],
    excluded: List[str],
    prefix="",
):
    props = document._doc_type.mapping.properties.properties
    ctx = RegistrationContext(
        model=model,
        serializer=serializer,
        mapping=serializer_mapping,
        prefix=prefix,
        included=included,
        excluded=excluded,
    )

    extra_fields = generate_mapping(prefix, ctx, serializer, included, excluded, props)

    if not extra_fields:
        return serializer
    return type(f"{document.__name__}Serializer", (serializer,), extra_fields)


def generate_mapping(prefix, ctx, existing_serializer, included, excluded, props):
    serializer_fields = existing_serializer().fields if existing_serializer else {}
    new_mapping = {}
    for fld_name in props:
        prefixed_name = prefix + fld_name
        if fld_name in serializer_fields:
            continue
        if included and prefixed_name not in included:
            continue
        if excluded and prefixed_name in excluded:
            continue
        fld = props[fld_name]
        new_mapping[fld_name] = generate_field_mapping(
            prefixed_name, fld_name, fld, ctx
        )
    return new_mapping


def generate_field_mapping(prefixed_name, fld_name, fld, ctx):
    if fld._multi:
        multi = True
    else:
        multi = False
    es_field_callable = get_serializer_field_from_es_field(prefixed_name, fld, ctx)
    if inspect.isclass(es_field_callable) and issubclass(es_field_callable, e.Field):
        ret = es_field_callable()
    elif callable(es_field_callable):
        ret = es_field_callable(fld_name, fld, ctx)
    else:
        raise ValueError(
            f"Bad value for field {prefixed_name}: expecting DSL field or callable, got {es_field_callable}"
        )
    if not multi:
        return ret
    return serializers.ListField(child=ret)


def get_serializer_field_from_es_field(prefixed_name, fld, ctx):
    if prefixed_name in ctx.mapping:
        return ctx.mapping[prefixed_name]

    for m in type(fld).mro():
        if m in ctx.mapping:
            return ctx.mapping[m]
    raise KeyError(
        f"Do not have Serializer mapping for ES field of type {type(fld)}. Either specify it in the `serializer_mapping` parameter"
        f"or exclude it with `excluded`"
    )
