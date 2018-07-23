from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from subtitle_app.models import Document, Translate, Suggestion
from .forms import DocumentForm, TranslateForm
import pysrt
from .languages import LANGUAGES
import datetime
import os
from tqdm import tqdm
from google.cloud import translate
from nltk import ngrams
import re
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
    "/Users/Elmas/Documents/django_projects/subtitle_translate_project/google_auth.json"



def n_gram(n, suggestion_list, test_sentence):
    # print("sentence", test_sentence)
    # train_dict kelimelerin 4(n)lü gruplar halinde olma olasılıklarını tutar.
    train_dict = {}
    # tüm suggestionların n'e göre split edilmiş hallerini split_list'e attık
    split_list = []
    # tüm suggestionların n-1'e göre split edilmiş hallerini minus_one_list'e attık
    minus_one_list = []
    # bu döngüde tüm suggestionların n ve n-1'e göre split eilmiş hallerini listeye attık.
    # Daha sonra bunların miktarlarına göre probability bulacağız.
    for suggestion in suggestion_list:
        ngrams_list = ngrams(re.findall(r"[\w']+|[.,!?;]", suggestion), n)
        for i in ngrams_list:
            split_list.append(list(i))
            minus_one_list.append(list(i)[:n-1])
    # bu döngüde her n'li grupların probabilitysini bulup train dict'e attık.
    for suggestion in suggestion_list:
        ngrams_list = ngrams(re.findall(r"[\w']+|[:().,!?;]", suggestion), n)
        for i in ngrams_list:
            minus_one_sentence = i[:n - 1]
            gram_probability = (split_list.count(list(i)) / minus_one_list.count(list(minus_one_sentence)))
            train_dict[i] = gram_probability
    # split_sentence test olarak verilen cümlenin split edilmiş ve nli gruplara ayrılmış tupleların listesi
    split_sentence = list(ngrams(re.findall(r"[\w']+|[.,!?;]", test_sentence), n))

    for i in range(0, len(split_sentence)):
        minus_one_sentence = split_sentence[i][:n - 1]
        # my brother is
        max_probability = 0
        max_part = ()
        # testdeki cümlemizin n-1 kadar kelimesini trainde olasılıklarını belirlediğimiz kelimeler ile
        # kıyaslayarak olasılığını bulmaya çalışıyoruz.
        for j in train_dict.keys():
            if minus_one_sentence == j[:n-1]:
                # en yüksek olasılığı bulmaya çalışıyoruz
                if train_dict[j] > max_probability:
                    max_probability = train_dict[j]
                    max_part = j
                    split_sentence[i] = tuple(max_part)
            else:
                pass

        if i < len(split_sentence) - 1:
            a = 0
            if len(split_sentence) < 4:
                for k in range(i, len(split_sentence)-1):
                    next_part = list(split_sentence[k + 1])
                    next_part[-a - 2] = split_sentence[i][-1]
                    split_sentence[k + 1] = tuple(next_part)
                    a = a + 1
            else:
                for k in range(i, 3):
                    next_part = list(split_sentence[k + 1])
                    next_part[-a - 2] = split_sentence[i][-1]
                    split_sentence[k + 1] = tuple(next_part)
                    a = a + 1
    return edit_sentence(split_sentence)


def edit_sentence(sentence_part_list):
    sentence_part_list = list(sentence_part_list)
    n = len(sentence_part_list)
    new_sentence = ""
    a = len(list(sentence_part_list[0]))
    for i in range(0, a):
        new_sentence = new_sentence + " " + str(sentence_part_list[0][i])
    if len(sentence_part_list) > 1:
        for i in range(1, n):
            new_sentence = new_sentence + " " + str(sentence_part_list[i][-1])
    return new_sentence


@login_required
def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            Document.objects.create(user=request.user, description=request.POST['description'],
                                    document=request.FILES['document'],
                                    source_language=request.POST['source_language'],
                                    target_language=request.POST['target_language'])
            return redirect('model_form_upload')
    else:
        form = DocumentForm()
    files = Document.objects.filter(user__id=request.user.id)
    return render(request, 'subtitle_app/subtitle_template.html',
                  {'form': form, 'files': files, 'LANGUAGES': LANGUAGES})


@login_required
def translation(request, pk):
    first = datetime.datetime.now()
    # if make suggestion
    if request.method == 'POST':
        form = TranslateForm(request.POST)
        if form.is_valid():
            # templatede hidden input ile suggestion yapılan translate objectinin idsini TranslateForm'a ekledik.
            # bu sayede sadece suggestion yapılan objecti elde edip(obj) onun üzerinde değişiklik yapmış olduk.
            obj = Translate.objects.get(id=form.cleaned_data['id'])
            obj.suggestion = form.cleaned_data['suggestion']
            obj.save()
    # eğer suggestion yapmıyorsak, sadece altyazıları görüntülüyorsak:
    # document pk yı url aracılığıyla gönderiyoruz
    else:
        file = Document.objects.get(pk=pk)
        subs = pysrt.open(file.document.path, encoding='iso-8859-1')
        length_subs = len(subs)
        # select_source_language = file.source_language
        select_target_language = file.target_language
        translate_object_list = []
        translate_client = translate.Client()
        for i in tqdm(range(0, length_subs)):
            sub = subs[i].text.replace("<i>", "").replace("</i>", "")
            if Translate.objects.filter(document__pk=pk).count() < length_subs:
                text = translate_client.translate(sub, target_language=select_target_language)
                translate_object_list.append(Translate(document=file, sentence=sub, suggestion='', edit_translation='',
                                                       translation=text['translatedText'].replace("&#39;", "")))
            else:
                break
        Translate.objects.bulk_create(translate_object_list)
    data = []
    for t in Translate.objects.filter(document__pk=pk):
        data.append((t, TranslateForm(initial={'id': t.id, 'suggestion': t.suggestion}, auto_id=True)))
    files = Document.objects.filter(user__id=request.user.id)

    for i in files:
        # aynı documentın translate leri
        same_document_translate_objects = Translate.objects.filter(document__id=i.id).exclude(suggestion='')
        for trans in same_document_translate_objects:
            # aynı translate cümlesinde tekrar bi öneri değişikliği yapılırsa update et.
            if trans.id not in Suggestion.objects.values_list("trans_id", flat=True):
                # get_or_create kllanmamızın sebebi her öneri yapıldığında tekrar aynı suggestion
                # objelerinin create edilmesini önlemek için
                Suggestion.objects.get_or_create(
                    user=request.user,
                    trans_id=trans.id,
                    suggestion_text=trans.suggestion)
            else:
                # eğer aynı sentenceın suggestionı değiştirilirse object i update  et.
                Suggestion.objects.filter(trans_id__contains=trans.id).update(suggestion_text=trans.suggestion)

    suggestion_list = Suggestion.objects.values_list('suggestion_text', flat=True)
    for i in files:
        # aynı documentın translate leri
        same_document_translate_objects = Translate.objects.filter(document__id=i.id)
        for trans in same_document_translate_objects:
            if len(trans.translation.split()) < 4:
                pass
            else:
                new_sentence = n_gram(4, suggestion_list, trans.translation)
                if not new_sentence == None:
                    Translate.objects.filter(id=trans.id).update(edit_translation=new_sentence)
                    # print("new_sentence", new_sentence)
                else:
                    pass
    second = datetime.datetime.now()
    print(second - first)
    return render(request, 'subtitle_app/trans.html', {'files': files, 'data': data, 'LANGUAGES': LANGUAGES})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            raw_password = form.cleaned_data['password1']
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('model_form_upload')
    else:
        form = UserCreationForm()
    return render(request, 'subtitle_app/signup.html', {'form': form})
