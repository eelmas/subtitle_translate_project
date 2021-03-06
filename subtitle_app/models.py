from django.db import models
from .languages import languages_tuple


class Document(models.Model):
    user = models.ForeignKey('auth.user', related_name='user', null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    source_language = models.CharField(max_length=250, blank=False, null=True, choices=languages_tuple)
    target_language = models.CharField(max_length=250, blank=False, null=True, choices=languages_tuple)

    def _str_(self):
        return self.document.name


class SubFile(models.Model):
    document = models.ForeignKey('subtitle_app.Document', related_name='documents',
                                 null=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=250, blank=True, null=True)
    time = models.CharField(max_length=250, blank=True, null=True)


class Translate(models.Model):
    document = models.ForeignKey('subtitle_app.Document', related_name='doct', null=True, on_delete=models.CASCADE)
    suggestion = models.CharField(max_length=250, blank=True, null=True)
    sentence = models.CharField(max_length=250, blank=True, null=True)
    translation = models.CharField(max_length=250, blank=True, null=True)
    edit_translation = models.CharField(max_length=250, blank=True, null=True)

    def _str_(self):
        return self.suggestion


class Suggestion(models.Model):
    user = models.ForeignKey('auth.user', related_name='suggestion_user', null=True, on_delete=models.CASCADE)
    trans_id = models.IntegerField(blank=True, null=True)
    suggestion_text = models.CharField(max_length=250, blank=True, null=True)
