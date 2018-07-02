from django.template.defaultfilters import register

@register.filter
def hash(h, key):
    return h[key]