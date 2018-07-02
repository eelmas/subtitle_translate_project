import os
from django.contrib.auth.decorators import login_required
import parser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from google.auth import credentials
import google.auth;
from subtitle_app.models import Document,Translate
from subtitle_translate_project import settings
from .forms import DocumentForm, TranslateForm
import pysrt
from django.contrib.auth.models import User
from googletrans import Translator
from .languages import LANGUAGES

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/Elmas/Downloads/project-57963f325379.json"

# Create your views here.


@login_required
def model_form_upload(request):
    if request.method == 'POST':

        form = DocumentForm(request.POST, request.FILES)

        #print(request.FILES)
        if form.is_valid():

            Document.objects.create(user=request.user, description=form.cleaned_data['description'], document=form.cleaned_data['document'],source_language=request.POST['source_language'],target_language=request.POST['target_language'])
            return redirect('model_form_upload')
    else :
        form = DocumentForm()

    files = Document.objects.filter(user__id=request.user.id)


    #print(Document.objects.all().values())
    #print(request.user.id)
    return render(request, 'subtitle_app/subtitle_template.html', {'form': form, 'files':files,'LANGUAGES':LANGUAGES})





def translate(request, pk):
    translator = Translator()



    if request.method == 'POST':
        form = TranslateForm(request.POST)
        if form.is_valid():
            obj = Translate.objects.get(id=form.cleaned_data['id'])
            obj.suggestion = form.cleaned_data['suggestion']
            obj.save()
    else:
        file = Document.objects.get(pk=pk)
        lines = []
        subs = pysrt.open(file.document.path, encoding='iso-8859-1')

        for i in range(0, len(subs)):
            sub = subs[i].text.replace("<i>", "").replace("</i>", "")
            lines.append(sub)
            l=len(subs)

            if(Translate.objects.filter(document__pk=pk).count()<l):
                select_source_language=file.source_language
                select_target_language=file.target_language


                translation=translator.translate(sub,src=select_source_language,dest=select_target_language)
                Translate.objects.create(document=file, sentence=sub, suggestion='', translation=translation.text)


    data = []
    for t in Translate.objects.filter(document__pk=pk):
        data.append((t, TranslateForm(initial={'id': t.id, 'suggestion': t.suggestion}, auto_id=True)))

    return render(request, 'subtitle_app/trans.html', {'data': data})




def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('model_form_upload')
    else:
        form = UserCreationForm()
    return render(request, 'subtitle_app/signup.html', {'form': form})
