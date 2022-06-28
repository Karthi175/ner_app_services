
from flask import Flask,request,make_response
from flask_cors import CORS,cross_origin

import re
import os
import json
import random

import time


import spacy
from spacy import displacy
from itertools import chain
from spacy.tokens import DocBin

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

class Restrict_Entities():

  gender_values = ["male","female","unknown","transgender"]
  marital_status_values = ["single","married","unknown","divorced","unmarried"]
  texts ={}

  def __init__(self,entity_header,ent,text,texts,extra_texts):
    self.entity_header = entity_header
    self.ent = ent
    self.text = text
    self.texts = texts
    self.extra_texts= extra_texts

  def verify_dob(self):

      if re.search(r"[\d]{1,2}[/:-—]+[\d]{1,2}[/:-—]+[\d]{2,4}",self.text): 
        year = re.search(r"[\d]{1,2}[/:-—]+[\d]{1,2}[/:-—]+[\d]{2,4}",self.text) 
        extracted_date = self.text[year.start():year.end()]
        remaining_text = self.text[year.end():]

        if re.search(r"[\w]*",remaining_text):
          self.extra_texts.append(self.text[year.end():])

        self.texts[self.ent.label_]=extracted_date

  def verify_phone(self):

      if re.search(r"[\d]+[-—]*[\d]+[-—]*[\d]+",self.text): 
        phone = re.search(r"[\d]+[-—]*[\d]+[-—]*[\d]+",self.text) 
        extracted_phone = self.text[phone.start():phone.end()]
        remaining_text = self.text[phone.end():]
        if re.search(r"[\w]*",remaining_text):
          self.extra_texts.append(self.text[phone.end():])
        self.texts[self.ent.label_]=extracted_phone

  def verify_gender(self):

    for gender in self.gender_values:
      if gender in self.text:
        self.texts[self.ent.label_]=self.text

  def verify_marital_status(self):

    for status in self.marital_status_values:
      if status in self.text:
        self.texts[self.ent.label_]=self.text

  def verify_email(self):

    email = re.search(r"[\s]*[\w]*[@]+[a-z]*[.]+[a-z]{2,3}",self.text)
    if email:
      extracted_email = self.text[email.start():email.end()]
      remaining_text = self.text[email.end():]
      if re.search(r"[\w]*",remaining_text):
          self.extra_texts.append(self.text[email.end():])
      self.texts[self.ent.label_]=extracted_email

  def verify_bloodGroup(self):

    blood_patterns = [r"[\s]*[a][\s]*[-][\s]*positive",r"[\s]*[a][\s]*[+][\s]*ve",r"[\s]*[a][\s]*[-][\s]*negative",r"[\s]*[a][\s]*[-][\s]*ve",r"[\s]*[b][\s]*[-][\s]*positive",
                      r"[\s]*[b][\s]*[+][\s]*ve",r"[\s]*[b][\s]*[-][\s]*negative",r"[\s]*[b][\s]*[-][\s]*ve","[\s]*[ab][\s]*[-][\s]*positive",r"[\s]*[ab][\s]*[+][\s]*ve",
                      r"[\s]*[ab][\s]*[-][\s]*negative",r"[\s]*[ab][\s]*[-][\s]*ve",r"[\s]*[o][\s]*[-][\s]*positive",r"[\s]*[o][\s]*[+][\s]*ve",r"[\s]*[o][\s]*[-][\s]*negative",
                      r"[\s]*[o][\s]*[-][\s]*ve"] 

    for blood_pattern in blood_patterns:
        
      if re.search(blood_pattern,self.text):
          group = re.search(blood_pattern,self.text)
          extracted = self.text[group.start():group.end()]
          remaining_text = self.text[group.end():]
          if re.search(r"[\w]*",remaining_text):
            self.extra_texts.append(self.text[group.end():])
          self.texts[self.ent.label_]=extracted
          break


  def map_entities(self):

    if self.ent.label_ == "DOB":
        self.text = self.ent.text[self.entity_header.end():]
        er_dob = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
        er_dob.verify_dob()

    if self.ent.label_ == "Address":
      self.texts[self.ent.label_] = self.ent.text

    if self.ent.label_ == "Name":
      self.text = self.ent.text[self.entity_header.end():]
      self.texts[self.ent.label_] = self.text

    if self.ent.label_ == "Ethnicity":
      self.texts[self.ent.label_] = self.ent.text

    if self.ent.label_ == "Gender":
      self.text = self.ent.text[self.entity_header.end():]
      er_gender = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_gender.verify_gender()

    if self.ent.label_ == "EmailID":
      self.text = self.ent.text[self.entity_header.end():]
      er_mail = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_mail.verify_email()

    if self.ent.label_ == "Blood Group":
      self.text = self.ent.text[self.entity_header.end():]
      er_mail = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_mail.verify_bloodGroup()

    if self.ent.label_ == "Marital Status":
      self.text = self.ent.text[self.entity_header.end():]
      er_marital_status = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_marital_status.verify_marital_status()

    if self.ent.label_ == "Phone" :
      self.text = self.ent.text[self.entity_header.end():]
      er_phone = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_phone.verify_phone()

    if self.ent.label_ == "SSN" :
      self.text = self.ent.text[self.entity_header.end():]
      er_ssn = Restrict_Entities(self.entity_header,self.ent,self.text,self.texts,self.extra_texts)
      er_ssn.verify_phone()
    

def detect_demographics(path_to_model,text):

  ner_demographics = spacy.load(path_to_model)
  text = text.lower()
  doc = ner_demographics(text)
  texts = {}
  extra_texts = []


  for ent in doc.ents:
    entity_header = re.search(r"[\s]*[a-zA-Z]*[\s]*[:-—]+",ent.text)

    if entity_header:

      er_map_entities = Restrict_Entities(entity_header,ent,text,texts,extra_texts)
      er_map_entities.map_entities()

      
  for text in extra_texts:
    if len(text)>0:
      doc = ner_demographics(text)
      for ent in doc.ents:
        if ent:
          entity_header = re.search(r"[\s]*[a-zA-Z]*[\s]*[:-—]+",ent.text)
          if entity_header:
            er_map_entities = Restrict_Entities(entity_header,ent,text,texts,extra_texts)
            er_map_entities.map_entities()


  # print(texts)
  return texts



CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
@app.route('/demo',methods=['POST'])
@cross_origin()
def demographics():
  dict1=request.get_data()
  dict1 = dict1.decode()
  # print(dict1)
  dict1 = json.loads(dict1)
  text=dict1['text']
  demo_res = detect_demographics("./demographics/model-best",text)
  demo_lis=[]
  for i,key in enumerate(demo_res):
    js={'id':i+1,'content':'','value':''}
    # print(key, ":", demo_res[key])
    js['content']=key
    val=demo_res[key].title()
    js['value']=val
    demo_lis.append(js)
  # print(demo_lis)
  return {'demo_res':demo_lis}

@app.route('/vitals',methods=['POST'])
@cross_origin()
def get_vitals():
  res_dict=request.get_data()
  res_dict = res_dict.decode()
  # print(res_dict)
  res_dict1 = json.loads(res_dict)
  text=res_dict1['text']
  dict1 = {}
  vital_model = spacy.load('./vitals/model-best')
  text = text.lower()
  doc = vital_model(text)
  entities = doc.ents
  count = len(entities)
  i=0
  while i<count:
    try:
      j=i+1
      label_pair = (entities[i].label_,entities[j].label_)
      if label_pair[0]=="vital_name" and label_pair[1]=="vital_value":
        # print(entities[i].text)
        # print(entities[j].text)
        ent_name = entities[i].text
        ent_value = entities[j].text
        ent_value = re.findall(r"[\d]+[.]*[\d]*[\s]*[\S]*",ent_value)[0]
        dict1[ent_name] = ent_value
        i = i+2
    except Exception as e:
      i=i+1
      pass
  vitals_lis=[]
  for i,key in enumerate(dict1.keys()):
    js={'id':i+1,'content':'','value':''}
    val=key.title()
    js['content']=val
    js['value']=dict1[key]
    vitals_lis.append(js)
  return {'vital_res':vitals_lis}

@app.route('/lab',methods=['POST'])
@cross_origin()
def get_lab_reports():
  dict1 = {}
  lb_model = spacy.load("./lab/model-best")
  res_dict=request.get_data()
  res_dict = res_dict.decode()
  # print(res_dict)
  res_dict1 = json.loads(res_dict)
  text=res_dict1['text']
  text = text.lower()
  doc = lb_model(text)

  entities = doc.ents
  count = len(entities)
  i=0
  while i<count:
    try:
      j=i+1
      label_pair = (entities[i].label_,entities[j].label_)

      if label_pair[0]=="lab_report_name" and label_pair[1]=="lab_report_value":
        # print(entities[i].text)
        # print(entities[j].text)
        ent_name = entities[i].text
        ent_name = ent_name.capitalize()
        ent_value = entities[j].text
        ent_value = re.findall(r"[\d]+[.]*[\d]*[\s]*[\S]*",ent_value)[0]
        dict1[ent_name] = ent_value
        i = i+2
    except Exception as e:
      i=i+1
      pass
  lab_lis=[]
  for i,key in enumerate(dict1.keys()):
    js={'id':i+1,'content':'','value':''}
    js['content']=key
    js['value']=dict1[key]
    lab_lis.append(js)
    # print(lab_lis)
  return {'lab_res':lab_lis}

  return dict1

# if __name__ == '__main__':
#   app.run()
