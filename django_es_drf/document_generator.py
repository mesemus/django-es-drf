import inspect
from typing import Type, List, Dict, Callable, Union

from django.db import models
import elasticsearch_dsl as e
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from django_es_drf.document_registry import RegistrationContext


def generate_extra_document_fields(
    document: Type[e.Document],
    model: Type[models.Model],
    serializer: Type[serializers.ModelSerializer],
    mapping: Union[
        Dict[
            Type[models.Field],
            Union[Callable[[serializers.Field], RegistrationContext], Type[e.Field]],
        ],
        Dict[
            str,
            Union[Callable[[serializers.Field], RegistrationContext], Type[e.Field]],
        ],
    ],
    included: List[str],
    excluded: List[str],
    prefix="",
):
    existing_mapping = document._doc_type.mapping
    ctx = RegistrationContext(
        model=model,
        serializer=serializer,
        mapping=mapping,
        prefix=prefix,
        included=included,
        excluded=excluded,
    )

    new_mapping = generate_mapping(
        prefix, ctx, existing_mapping, included, excluded, serializer
    )

    if not new_mapping:
        return document
    return type(document.__name__, (document,), new_mapping)


def generate_mapping(prefix, ctx, existing_mapping, included, excluded, serializer):
    new_mapping = {}
    if inspect.isclass(serializer):
        serializer = serializer()

    for fld_name, fld in serializer.fields.items():
        prefixed_name = prefix + fld_name
        if included and prefixed_name not in included:
            continue
        if excluded and prefixed_name in excluded:
            continue
        if fld_name in existing_mapping:
            continue
        # TODO: generate object and nested here
        if isinstance(fld, ListSerializer):
            multi = True
            fld = fld.child
        else:
            multi = False
        es_field_callable = get_es_field_from_serializer_field(prefixed_name, fld, ctx)
        if inspect.isclass(es_field_callable) and issubclass(
            es_field_callable, e.Field
        ):
            new_mapping[fld_name] = es_field_callable(multi=multi)
        elif callable(es_field_callable):
            new_mapping[fld_name] = es_field_callable(fld_name, fld, ctx, multi=multi)
        else:
            raise ValueError(
                f"Bad value for field {prefixed_name}: expecting DSL field or callable, got {es_field_callable}"
            )
    return new_mapping


def get_es_field_from_serializer_field(prefixed_name, fld, ctx):
    if prefixed_name in ctx.mapping:
        return ctx.mapping[prefixed_name]

    for m in type(fld).mro():
        if m in ctx.mapping:
            return ctx.mapping[m]
    raise KeyError(
        f"Do not have ES mapping for {type(fld)}. Either specify it in the `mapping` parameter"
        f"or exclude it with `excluded`"
    )
