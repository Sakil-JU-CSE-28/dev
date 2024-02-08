import csv
import os
import sys
import re
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Message
from django.apps import apps

word_probability = {}
label_word_count = {}
label_probability = {}

def delete_all_instances():
    all_models = apps.get_models()
    for model in all_models:
        model.objects.all().delete()

def preprocess(raw_text):
  raw_text = raw_text.lower()
  stop_words = set([".", ",", "!", "?", "$", "%","#","@","*","+","-"])
  tokens = re.findall(r'\b\w+\b', raw_text)
  removed_stopwords = [word for word in tokens if word not in stop_words]
  processed_text = ' '.join(removed_stopwords)
  return processed_text

def PushData():
   csv_file_path = os.path.join(settings.BASE_DIR, 'C:/Users/Lab1/projectDir/SpamMsgDetector/spam.csv')
   with open(csv_file_path, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  
        for row in csv_reader:
         if len(row) >= 2:
            msg_type = row[0]
            msg = ','.join(row[1:])
            msg = preprocess(msg)
            message = Message(type=msg_type,msg = msg)
            message.save()
         else:
          print(f"Ignoring row: {row} - Expected 2 columns, found {len(row)}")

def Home(request):
    firstpage = loader.get_template('home.html')
    return HttpResponse(firstpage.render())

def SpamDetector(request):
    all_messages = Message.objects.all()
    msg_list = [message.msg for message in all_messages]
    type_list = [message.type for message in all_messages]
    fit(msg_list,type_list)
    if request.method == 'POST':
        full_text = request.POST.get('full_text', '') 
        response = predict(full_text)
        suggestion = ""
        if response == "spam":
          suggestion = "Warning: This message might be spam!"
        else:
          suggestion = "No spam detected. Your message is safe."
        remember = Message(msg = preprocess(full_text),type = response)
        remember.save()
        return render(request, 'result_template.html', {'message': suggestion})
    return render(request, 'inputForm.html')

def fit(X_train, y_train):
    words = set()
    original_data = zip(X_train,y_train)
    for message,label in original_data:
     if label not in word_probability:
      word_probability[label] = {}
      label_word_count[label] = 0
     for word in str(message).split(' '):
      if word not in word_probability[label]:
        word_probability[label][word] = 1
        label_word_count[label] = label_word_count[label] + 1
      words.add(word)
      word_probability[label][word] = word_probability[label][word] + 1
      label_word_count[label] = label_word_count[label] + 1
    for key,value in word_probability.items():
      for word in value:
        if word not in words:
         word_probability[key][word] = 1
         label_word_count[key] = label_word_count[key] + 1
    for key,value in word_probability.items():
      for word in value:
        word_probability[key][word] = word_probability[key][word] / label_word_count[key];
    total = 0
    for label in y_train:
      if label not in label_probability:
        label_probability[label] = 0
      label_probability[label] = label_probability[label] + 1
      total = total + 1
    for key,value in label_probability.items():
      label_probability[key] = label_probability[key] / total;

def predict(message):
  message = preprocess(message)
  words = str(message).split(' ')
  spam_probability = 0
  ham_probability = 0
  for word in words:
    if "spam" in word_probability and word in word_probability["spam"]:
      spam_probability = label_probability["spam"] * word_probability["spam"][word]
    if "ham" in word_probability and word in word_probability["ham"]:
      ham_probability = label_probability["ham"] * word_probability["ham"][word]
  probable_label = ' '
  if ham_probability > spam_probability:
    probable_label = "ham"
  else:
    probable_label = "spam"
  return probable_label
