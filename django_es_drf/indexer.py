import contextlib
import contextlib
import threading

from django.conf import settings
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import get_connection

es_lock = threading.local()


def es_locked():
    return getattr(es_lock, "locked", False)


def es_disabled():
    return getattr(es_lock, "disabled", False)


def es_index(obj, force=False):
    if es_disabled():
        return

    if es_locked():
        if not hasattr(es_lock, "objects"):
            es_lock.objects = []
        es_lock.objects.append((obj, False))
        es_flush(force)
    else:
        es_index_internal([(obj, False)])


def es_delete(obj, force=False):
    if es_disabled():
        return

    if es_locked():
        if not hasattr(es_lock, "objects"):
            es_lock.objects = []
        es_lock.objects.append((obj, True))
        es_flush(force)
    else:
        es_index_internal([(obj, True)])


def es_flush(force=False, refresh=False):
    objects = getattr(es_lock, "objects", [])
    if not force and len(objects) < getattr(settings, "ES_INDEX_BATCH", 200):
        return
    try:
        es_index_internal(objects, refresh=refresh)
    finally:
        es_lock.objects = []
        pass


def upsert(id, body, index):
    d = {}
    d["_op_type"] = "update"
    d["_index"] = index
    d["doc"] = body
    d["doc_as_upsert"] = True
    if id:
        d["_id"] = id
    return d


def es_index_internal(objects, refresh=True):
    from .document_registry import registry

    if not objects:
        return
    actions = []
    for obj, should_delete in objects:
        idx, _id, data = registry.model_to_index_and_id_and_data(obj)

        if should_delete and _id:
            actions.append({"_op_type": "delete", "_index": idx, "_id": _id})
        else:
            actions.append(upsert(id=_id, body=data, index=idx))

    ret = bulk(get_connection("default"), actions, stats_only=True, refresh=refresh)
    return ret


@contextlib.contextmanager
def bulk_es(bulk=True):
    es_lock.locked = bulk
    try:
        yield
        es_flush(True)
    finally:
        es_lock.locked = False


@contextlib.contextmanager
def disabled_es():
    es_lock.disabled = True
    try:
        yield
    finally:
        es_lock.disabled = False
