from django.contrib import admin
from .models import Document, Translate, Suggestion


admin.site.register(Document)
admin.site.register(Translate)
admin.site.register(Suggestion)

# Register your models here.
