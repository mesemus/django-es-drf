from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from . import registry
from .indexer import es_delete, es_index


def data_saved(sender, instance=None, **kwargs):
    es_index(instance)


def data_deleted(sender, instance=None, **kwargs):
    es_delete(instance)


@receiver(m2m_changed)
def m2m_hook(sender, instance, action, **kwargs):
    if not action.startswith("post_"):
        return
    try:
        registry.get_registry_entry_from_django(type(instance))
        es_index(instance)
    except KeyError:
        return
