import os
import time
import self
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
from itertools import islice
import datetime
import os
from tqdm import tqdm
from google.cloud import translate
from hyper.contrib import HTTP20Adapter
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/Elmas/Documents/django_projects/subtitle_translate_project/google_auth.json"
# GOOGLE_APPLICATION_CREDENTIALS="/Users/Elmas/Documents/django_projects/subtitle_translate_project/My\ Project\ 97243-204eb4c3ef96.json"
from googletrans import urls, utils


@login_required
def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            a=Document.objects.create(user=request.user, description=form.cleaned_data['description'], document=form.cleaned_data['document'],source_language=request.POST['source_language'],target_language=request.POST['target_language'])
            print(a)
            return redirect('model_form_upload')
    else :
        form = DocumentForm()
    files = Document.objects.filter(user__id=request.user.id)
    return render(request, 'subtitle_app/subtitle_template.html', {'form': form, 'files':files,'LANGUAGES':LANGUAGES})


def translation(request, pk):
    first=datetime.datetime.now()
    #if make suggestion
    if request.method == 'POST':
        form = TranslateForm(request.POST)
        if form.is_valid():
            #templatede hidden input ile suggestion yapılan translate objectinin idsini TranslateForm'a ekledik.
            #bu sayede bu sayede sadece suggestion yapılan objecti elde edip(obj) onun üzerinde değişiklik yapmış olduk.
            obj = Translate.objects.get(id=form.cleaned_data['id'])
            obj.suggestion = form.cleaned_data['suggestion']
            obj.save()
    #eğer suggestion yapmıyorsak, sadece altyazıları görüntülüyorsak:
    #document pk yı url aracılığıyla gönderiyoruz
    else:
        file = Document.objects.get(pk=pk)
        subs = pysrt.open(file.document.path, encoding='iso-8859-1')
        l = len(subs)
        select_source_language = file.source_language
        select_target_language = file.target_language
        translate_object_list = []
        translate_client = translate.Client()
        for i in tqdm(range(0, l)):
            sub = subs[i].text.replace("<i>", "").replace("</i>", "")
            text = translate_client.translate(sub, target_language=select_target_language)
            if Translate.objects.filter(document__pk=pk).count() < l:
                translate_object_list.append(Translate(document=file, sentence=sub, suggestion='',translation=text['translatedText']))
            else:
                break
        Translate.objects.bulk_create(translate_object_list)
    data = []
    for t in Translate.objects.filter(document__pk=pk):
        data.append((t, TranslateForm(initial={'id': t.id, 'suggestion': t.suggestion}, auto_id=True)))
    files = Document.objects.filter(user__id=request.user.id)
    second=datetime.datetime.now()
    print(second-first)
    return render(request, 'subtitle_app/trans.html', {'files': files,'data': data,'LANGUAGES': LANGUAGES})


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
