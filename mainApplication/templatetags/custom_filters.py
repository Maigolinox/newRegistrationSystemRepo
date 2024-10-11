from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get the item from the dictionary."""
    return dictionary.get(key, None)