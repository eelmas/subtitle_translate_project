from django import forms
from .models import Document,Translate


class DocumentForm(forms.ModelForm):
    #language = forms.ModelMultipleChoiceField(choices=languages_tuple, required=False)

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        self.fields['document'].widget.attrs.update({'id': 'id_document', 'class': 'custom-file-input','required':''})
        self.fields['description'].widget.attrs.update({'id': 'id_description','class': 'form-control','placeholder':"Enter file name"})
        self.fields['source_language'].widget.attrs.update({'id':"id_source_language",'class': 'form-control'})
        self.fields['target_language'].widget.attrs.update({'id':"id_target_language",'class': 'form-control','required':''})


    class Meta:
        model = Document
        fields = ('document', 'description','source_language','target_language' )




class TranslateForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    suggestion = forms.CharField()
