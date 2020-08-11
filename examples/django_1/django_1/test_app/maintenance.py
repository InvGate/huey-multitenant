from django.core.cache import cache


def is_in_maintenance():
    return cache.get("maintenance", default=False)


def set_maintenance(value):
    cache.set("maintenance", value)
