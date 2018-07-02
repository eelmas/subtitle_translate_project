from django import forms
from .models import Document,Translate


class DocumentForm(forms.ModelForm):
    #language = forms.ModelMultipleChoiceField(choices=languages_tuple, required=False)

    class Meta:
        model = Document
        fields = ('description', 'document','source_language','target_language' )


class TranslateForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    suggestion = forms.CharField()
