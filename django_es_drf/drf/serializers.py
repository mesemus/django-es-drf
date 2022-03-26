from typing import Type

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer, Serializer


class ESDocumentSerializer(BaseSerializer):
    django_serializer: Type[Serializer]

    def __init__(self, *args, django_serializer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.django_serializer = django_serializer

    def to_internal_value(self, data):
        serializer = self.django_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        if data.keys() != serializer.validated_data.keys():
            raise ValidationError(
                f"Unexpected keys {data.keys() - serializer.validated_data.keys()}"
            )
        return serializer.validated_data

    def to_representation(self, instance):
        # just return the document
        return instance

    def create(self, validated_data):
        document_class = self.context["view"].document
        # TODO: nested are not supported
        doc = document_class(**validated_data)
        doc.save()
        return doc

    def update(self, instance, validated_data):
        if self.partial:
            for k, v in validated_data.items():
                setattr(instance, k, v)
        else:
            # clear the instance
            doctype = type(instance)
            if doctype.DOCUMENT_ID_FIELD not in validated_data:
                validated_data[doctype.DOCUMENT_ID_FIELD] = instance.meta.id
            instance = doctype(meta={"id": instance.meta.id}, **validated_data)
        instance.save()
        return instance
