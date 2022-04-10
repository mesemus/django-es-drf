from elasticsearch_dsl import Document, Object
from elasticsearch_dsl.utils import DOC_META_FIELDS

from .indexer import disabled_es
from .indexer import es_index
from .document_registry import registry


class DjangoDocument(Document):
    DOCUMENT_ID_FIELD = "id"
    DJANGO_ID_FIELD = "pk"

    def save(self, **kwargs):
        django_object = kwargs.pop("django_object", None)
        with disabled_es():
            # do not save to elasticsearch inside this block as we will call super below
            obj = registry.save_to_django_object(self, django_object=django_object)
        _id = getattr(obj, self.DJANGO_ID_FIELD)
        setattr(self, self.DOCUMENT_ID_FIELD, _id)
        self.meta._id = _id
        self.meta.id = _id
        self.full_clean()
        es_index(self)

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

    def to_dict(self, include_meta=False, skip_empty=True):
        d = super(Document, self).to_dict(skip_empty=True)
        if not skip_empty:
            _mapping = self._doc_type.mapping
            for fld_name in _mapping:
                fld = _mapping[fld_name]
                if fld_name not in d:
                    if fld._multi:
                        d[fld_name] = []
                    elif isinstance(fld, Object):
                        d[fld_name] = {}
                    else:
                        d[fld_name] = None

        if not include_meta:
            return d

        meta = {"_" + k: self.meta[k] for k in DOC_META_FIELDS if k in self.meta}

        # in case of to_dict include the index unlike save/update/delete
        index = self._get_index(required=False)
        if index is not None:
            meta["_index"] = index

        meta["_source"] = d
        return meta
