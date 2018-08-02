#!/usr/bin/python

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from subtitle_app.models import Document, Translate, Suggestion, SubFile
from .forms import DocumentForm, TranslateForm
import pysrt
from .languages import LANGUAGES
import datetime
import os
from tqdm import tqdm
from google.cloud import translate
from nltk import ngrams
import re
import os.path
from chardet.universaldetector import UniversalDetector
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
    "/Users/Elmas/Documents/django_projects/subtitle_translate_project/google_auth.json"


def calculate_train_probability(n, suggestion_list):
    # train_dict holds the probability that the words are in groups.
    train_dict = {}
    # split all the suggestions into n split_list
    split_list = []
    # I split all suggestions into n-1 split states into minus_one_list
    minus_one_list = []
    # in this loop we list all the suggestions split into n and n-1.
    # We will then find a probability based on their quantities.
    for suggestion in suggestion_list:
        suggestion.replace("<i>", "")
        ngrams_list = ngrams(re.findall(r"[\w']+|[.,!?;]", suggestion), n)
        for i in ngrams_list:
            split_list.append(list(i))
            minus_one_list.append(list(i)[:n - 1])
    # in this loop we found the probability of each group of n and went to train_dict.
    for suggestion in suggestion_list:
        ngrams_list = ngrams(re.findall(r"[\w']+|[:().,!?;]", suggestion), n)
        for i in ngrams_list:
            minus_one_sentence = i[:n - 1]
            gram_probability = (split_list.count(list(i)) / minus_one_list.count(list(minus_one_sentence)))
            train_dict[i] = gram_probability
    return train_dict


def n_gram(n, train_dict, test_sentence):
    # split_sentence List of tuples split into nested groups that are given as test
    split_sentence = list(ngrams(re.findall(r"[\w']+|[.,!?;]", test_sentence), n))
    for i in range(0, len(split_sentence)):
        minus_one_sentence = split_sentence[i][:n - 1]
        max_probability = 0
        max_part = ()
        # we are trying to find out the possibility of comparing the probability of
        #  n-1 sentences in the test with the words that we have determined.
        for train in train_dict.keys():
            minus_one_sentence2 = ()
            minus_one_train = train[:n-1]
            for l in minus_one_sentence:
                minus_one_sentence2 = minus_one_sentence2 + (l.lower(),)
            minus_one_train2 = ()
            for g in minus_one_train:
                minus_one_train2 = minus_one_train2+(g.lower(),)
            if minus_one_sentence2 == minus_one_train2:
                # we are trying to find the highest probability
                if train_dict[train] > max_probability:
                    max_probability = train_dict[train]
                    max_part = train
                split_sentence[i] = tuple(max_part)
            # the sentence remains at the beginning.
            else:
                pass

        # a change is made to a member of split_sentence above
        # at the bottom, this change applies to all the elements that are modified
        if i < len(split_sentence) - 1:
            a = -2
            if len(split_sentence) < n:
                for k in range(i, len(split_sentence)-1):
                    next_part = list(split_sentence[k + 1])
                    next_part[a] = split_sentence[i][-1]
                    split_sentence[k + 1] = tuple(next_part)
                    a = a - 1
            else:
                for k in range(i, n-1):
                    next_part = list(split_sentence[k + 1])
                    next_part[a] = split_sentence[i][-1]
                    split_sentence[k + 1] = tuple(next_part)
                    a = a - 1
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
    new_sentence = re.sub(r' ([^A-Za-z0-9])', r'\1', new_sentence)
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


def detect(file):
    # file = Document.objects.get(pk=pk)
    detector = UniversalDetector()
    for line in open(file.document.path, 'rb'):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    return detector.result


@login_required
def translation(request, pk):
    first = datetime.datetime.now()
    document_path_template = ""
    # if make suggestion
    if request.method == 'POST':
        form = TranslateForm(request.POST)
        if form.is_valid():
            # In the template we added the id of the translate object suggested to the TranslateForm with hidden input.
            # we only get the suggestion object and make changes on it.
            obj = Translate.objects.get(id=form.cleaned_data['id'])
            obj.suggestion = form.cleaned_data['suggestion']
            obj.save()
    # if we are not suggestion, if we are only viewing subtitles: we send document PK via url
    else:
        file = Document.objects.get(pk=pk)
        encode = detect(file)
        extension = os.path.splitext(file.document.path)[1]
        length_subs = 0
        if extension == '.sub':
            sub_file = open(file.document.path, encoding=encode.get('encoding'))
            read_file = sub_file.read()
            pattern = "\n\n"
            # match = re.search(pattern, read_file)
            lines = read_file.split("\n\n")
            length_subs = len(lines)
            sublist_object_list = []
            for l in range(0, len(lines)):
                sub = ""
                line = lines[l].split("\n")
                for i in range(1, len(line)):
                    sub += line[i] + " "
                if len(SubFile.objects.filter(document__pk=pk)) < length_subs:
                    print(sub)
                    sublist_object_list.append(SubFile(document=file, text=sub,
                                                       time=line[0]))
            SubFile.objects.bulk_create(sublist_object_list)
            print(SubFile.objects.all().values())
            subs = SubFile.objects.filter(document__pk=pk)
        elif extension == '.srt':
            subs = pysrt.open(file.document.path, encoding='iso-8859-9')
            length_subs = len(subs)
        select_target_language = file.target_language
        translate_object_list = []
        translate_client = translate.Client()
        for i in tqdm(range(0, length_subs)):
            sub = subs[i].text
            if Translate.objects.filter(document__pk=pk).count() < length_subs:
                text = translate_client.translate(sub, target_language=select_target_language)
                translate_object_list.append(Translate(document=file, sentence=sub, suggestion='', edit_translation='',
                                                       translation=text['translatedText']))
            else:
                break
        Translate.objects.bulk_create(translate_object_list)
        # document_path_template = create_srt_file(subs, pk)
        if extension == ".sub":
            document_path_template = create_sub_file(subs, pk)
        elif extension == ".srt":
            document_path_template = create_srt_file(subs, pk)
    data = []
    for t in Translate.objects.filter(document__pk=pk):
        data.append((t, TranslateForm(initial={'id': t.id, 'suggestion': t.suggestion}, auto_id=True)))
    files = Document.objects.filter(user__id=request.user.id)

    get_suggestion(files, request)
    suggestion_list = Suggestion.objects.values_list('suggestion_text', flat=True)
    n = 3
    for i in files:
        # the same document translations
        same_document_translate_objects = Translate.objects.filter(document__id=i.id)
        for trans in same_document_translate_objects:
            if len(trans.translation.split()) < n:
                pass
            else:
                # train_dict = dictionary which holds the probabilities of suggestion
                train_dict = calculate_train_probability(n, suggestion_list)
                new_sentence = n_gram(n, train_dict, trans.translation)
                if not new_sentence == None:
                    b = str(Translate.objects.filter(id=trans.id).values_list('translation', flat=True)[0])
                    a = re.sub(r'[^\w\s]', '', b)
                    new_sentence2 = re.sub(r'[^\w\s]', '', new_sentence)
                    if new_sentence2.replace(" ", "") != a.replace(" ", ""):
                        Translate.objects.filter(id=trans.id).update(edit_translation=new_sentence[1:].
                                                                     replace("39;", "'").replace("quot;", '"'))

                else:
                    pass
    second = datetime.datetime.now()
    print(second - first)

    return render(request, 'subtitle_app/trans.html', {'files': files, 'data': data, 'LANGUAGES': LANGUAGES,
                                                       'document_path_template': document_path_template})


def create_srt_file(subs, pk):
    length_subs = len(subs)
    for i in range(0, length_subs):
        subs[i].text = Translate.objects.filter(document__pk=pk)[i].translation
    document_name = str(Translate.objects.filter(document__pk=pk)[0].document.document)[10:]
    document_path = '/Users/Elmas/Documents/django_projects/subtitle_translate_project/media/new_srt_files/' \
                    + document_name
    subs.save(document_path, encoding='utf-8')
    document_path_template = '/media/new_srt_files/' + document_name
    return document_path_template


def create_sub_file(subs, pk):
    length_subs = len(subs)
    print(length_subs)
    for i in range(0, length_subs):
        subs[i].text = Translate.objects.filter(document__pk=pk)[i].translation
    document_name = str(
        Translate.objects.filter(document__pk=pk)[i].document.document)[10:]
    document_path = '/Users/Elmas/Documents/django_projects/subtitle_translate_project/media/new_srt_files/' \
                    + document_name
    document_path_template = '/media/new_srt_files/' + document_name
    f = open(document_path, "w+")
    for i in range(0, length_subs):
        f.write(subs[i].time)
        f.write("\n")
        f.write(subs[i].text)
        f.write("\n")
        f.write("\n")
    return document_path_template


@login_required
def file_remove(request, pk):
    file = get_object_or_404(Document, pk=pk)
    file.delete()
    return redirect('model_form_upload')


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


# Generate suggestion model objects from suggestions.
def get_suggestion(files, request):
    for i in files:
        # suggestions in the translate objects of the same document
        same_document_translate_objects = Translate.objects.filter(document__id=i.id).exclude(suggestion='')
        for trans in same_document_translate_objects:
            if trans.id not in Suggestion.objects.values_list("trans_id", flat=True):
                # Whenever we make use of get_or_create, we make sure that the same suggestion
                # objects are not created again.
                Suggestion.objects.get_or_create(
                    user=request.user,
                    trans_id=trans.id,
                    suggestion_text=trans.suggestion)
            else:
                # update the object if the same sentence's suggestion is changed.
                Suggestion.objects.filter(trans_id__contains=trans.id).update(suggestion_text=trans.suggestion)
