from collections import namedtuple
from dataclasses import dataclass
from typing import Type, Dict

from elasticsearch_dsl import Document
from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from . import settings
from .drf.serializers import StrictModelSerializer
from .indexer import disabled_es
from .json import to_plain_json

from django.db.models.signals import post_save, post_delete

import lazy_object_proxy


@dataclass
class DocumentRegistryEntry:
    model: Type[Model]
    document: Type[Document]
    serializer: Type[ModelSerializer]


class DjangoDocument(Document):
    DOCUMENT_ID_FIELD = "id"
    DJANGO_ID_FIELD = "pk"

    def save(self, **kwargs):
        with disabled_es():
            # do not save to elasticsearch inside this block as we will call super below
            obj = registry.save_to_django_object(self)
            obj.save()
        _id = getattr(obj, self.DJANGO_ID_FIELD)
        setattr(self, self.DOCUMENT_ID_FIELD, _id)
        self.meta._id = _id
        self.meta.id = _id
        if "refresh" not in kwargs:
            kwargs["refresh"] = True
        return super().save(**kwargs)

    def delete(self, using=None, index=None, **kwargs):
        entry = registry.get_registry_entry_from_document(type(self))
        obj = entry.model.objects.get(**{self.DJANGO_ID_FIELD: self.meta.id})
        with disabled_es():
            obj.delete()
        if "refresh" not in kwargs:
            kwargs["refresh"] = True
        return super().delete(using=using, index=index, **kwargs)

    @classmethod
    def from_django(cls, pk):
        return registry.load_from_django_object(cls, pk)

    def to_django(self):
        return registry.save_to_django_object(self)


RegistrationContext = namedtuple(
    "RegistrationContext", "model, serializer, mapping, prefix, included, excluded"
)


class DocumentRegistry:
    def __init__(self):
        self.by_model = {}
        self.by_document = {}

    def register(
        self,
        model: Type[Model],
        serializer: Type[ModelSerializer] = None,
        serializer_meta: Dict[str, any] = None,
        generate=True,
        included=(),
        excluded=(),
        mapping=None,
        serializer_mapping=None,
    ):
        """
        A decorator that registers a model with a DSL document. Usage

        @registry.register(MyModel)
        class MyModelDocument(DjangoDocument):
            class Index:
                name="blah"

        :param model:           django model
        :param serializer:      optional DRF serializer to turn the model into document's data
        :param serializer_meta: if serializer is not passed and is generated automatically, this
                                will be used to extend the meta of the serializer
        :param generate:        automatically generate fields not present on the document
        :param included:        list of fields to include in the document. Empty means all fields
        :param excluded:        list of fields to exclude from the document. Empty means all fields
        :param mapping:         a dictionary that specifies the mapping between DRF serializer fields
                                and Document fields. There are multiple cases
                                * key is a DRF field class, value a Document field class
                                * key is a DRF field class, value a callable(field: DRFField, context: RegistrationContext)
                                  that returns a Document field class or directly a Document field instance
                                * key is a string with field name(with optional dot notation), value a Document field
                                  class or a callable as above
                                * key is a string with field name (with optional dot notation), value a dict of parameters
                                  that will be added to field's constructor
        :return:                decorator
        """
        mapping = {**settings.DJANGO_ES_DEFAULT_FIELD_MAPPING, **(mapping or {})}
        serializer_mapping = {
            **settings.ES_DRF_DEFAULT_FIELD_MAPPING,
            **(serializer_mapping or {}),
        }

        if serializer is None:
            # generate serializer if not passed
            serializer = type(
                f"{model.__name__}Serializer",
                (StrictModelSerializer,),
                {
                    "Meta": type(
                        "Meta",
                        (),
                        {"model": model, "exclude": (), **(serializer_meta or {})},
                    )
                },
            )

        def do_registration(document, model, serializer):
            entry = DocumentRegistryEntry(
                model=model, document=document, serializer=serializer
            )
            self.by_model[model] = entry
            self.by_document[document] = entry

            from .signals import data_saved, data_deleted

            post_save.connect(data_saved, sender=model)
            post_delete.connect(data_deleted, sender=model)

        def delayed_registration(document, model, serializer):
            from .document_generator import generate_extra_document_fields
            from django_es_drf.serializer_generator import (
                generate_extra_serializer_fields,
            )

            document = generate_extra_document_fields(
                document, model, serializer, mapping, included, excluded
            )
            serializer = generate_extra_serializer_fields(
                document, model, serializer, serializer_mapping, included, excluded
            )
            do_registration(document, model, serializer)
            return document

        def wrapper(document: Type[Document]):
            if generate:
                return lazy_object_proxy.Proxy(
                    lambda: delayed_registration(document, model, serializer)
                )
            else:
                do_registration(document, model, serializer)
                return document

        return wrapper

    def save_to_django_object(self, document, django_object=None):
        entry = self.get_registry_entry_from_document(type(document))
        data = to_plain_json(document)
        try:
            id = getattr(document, document.DOCUMENT_ID_FIELD)
        except:
            id = None
        if django_object is None:
            if id is not None:
                django_object = entry.model.objects.filter(
                    **{document.DJANGO_ID_FIELD: id}
                ).first()
        serializer = entry.serializer(data=data)
        serializer.is_valid(True)

        if not django_object:
            return serializer.create(serializer.validated_data)
        else:
            return serializer.update(django_object, serializer.validated_data)

    def load_from_django_object(self, documentType: Type[Document], obj_or_pk):
        entry = self.get_registry_entry_from_document(documentType)
        if not isinstance(obj_or_pk, entry.model):
            obj = entry.model.objects.get(**{documentType.DJANGO_ID_FIELD: obj_or_pk})
        else:
            obj = obj_or_pk
        serializer = entry.serializer(instance=obj)
        return documentType(
            meta={
                "id": getattr(obj, documentType.DJANGO_ID_FIELD),
            },
            **serializer.data,
        )

    def model_to_index_and_id_and_data(self, obj):
        entry = self.get_registry_entry_from_django(type(obj))
        doc = self.load_from_django_object(entry.document, obj)
        return doc._index._name, doc.meta.id, to_plain_json(doc)

    def get_registry_entry_from_document(
        self, document: Type[Document]
    ) -> DocumentRegistryEntry:
        for m in document.mro():
            if m in self.by_document:
                return self.by_document[m]
        raise KeyError(
            f"Document of type {document} not found in django document registry"
        )

    def get_registry_entry_from_django(
        self, django: Type[Model]
    ) -> DocumentRegistryEntry:
        for m in django.mro():
            if m in self.by_model:
                return self.by_model[m]
        raise KeyError(
            f"Django object of type {django} not found in django document registry"
        )


registry = DocumentRegistry()
