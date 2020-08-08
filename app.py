# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 10:35:54 2020

@author: ACER
"""

from flask import Flask, request, render_template
from bs4 import BeautifulSoup as bs
import requests
import pickle
from datetime import date
import json


app = Flask(__name__)

with open('senti_clf.pkl', 'rb') as f:
    loaded_new_clf = pickle.load(f)

with open('vectorizer_org.pkl', 'rb') as f:
    loaded_vect = pickle.load(f)

@app.route("/")
def index():

    course_list = []
    
    with open("course_details.json", "r") as f:
        stored_courses = json.load(f)
    
    for course in stored_courses['courses']:
        course_list.append([course['name'], course['title']])
        print(course_list)

    return render_template("index.html", course_list = course_list)

@app.route("/display/<link>", methods = ["POST", "GET"])
def display(link):
    ncount = 0
    pcount = 0
    title = ""
    labels = ["POSITIVE", "NEGATIVE"]
    print(link)
    
    with open("course_details.json", "r") as f:
        stored_courses = json.load(f)
        
    for course in stored_courses['courses']:
        if link == course['name']:
            pcount = course['pcount']
            ncount = course['ncount']
            title = course['title'] 

    values = [pcount, ncount]

    return render_template("predictions.html", labels = labels, values = values, title = title)
    
@app.route("/predict", methods = ["POST"])
def predict():    
    org_str = request.form["website"]
    index = org_str.find('/learn/') + len('/learn/')
    end_index = org_str.find('/', index)
    spec_index = org_str.find('?', index)
    rev_index = org_str.find('#', index)
                             
    if end_index != -1:
        course_name = org_str[index:end_index]
    elif spec_index != -1:
        course_name = org_str[index:spec_index]
    elif rev_index != -1:
        course_name = org_str[index:rev_index]
    else:
        course_name = org_str[index:]
        
    ncount = 0
    pcount = 0
    title = ""
    
    labels = ["POSITIVE", "NEGATIVE"]
    flag = True
    
    with open("course_details.json", "r") as f:
        stored_courses = json.load(f)
        
    for course in stored_courses['courses']:
        if course_name == course['name']:
            pcount = course['pcount']
            ncount = course['ncount']
            title = course['title']
            flag = False
            
            
    if flag:
        n = 0
        total_comments = []
        
        while True:
            n += 1
            url = "https://www.coursera.org/learn/{}/reviews?page={}".format(course_name, n)
            r = requests.get(url)
            rec_url = "https://www.coursera.org/learn/{}".format(course_name)
            p = bs(requests.get(rec_url).content, "lxml")
            #print("You have reached inside scraper and given the url which is: ", url)
            page = bs(r.content, "lxml")
            
            comments = []
        
            for review in page.find_all("div", attrs = {"class" : "reviewText"}):
                comments.append(review.get_text())
                
            if(len(comments) > 0):
                for i in comments:
                    total_comments.append(i)
            else:
                break

            for heading in p.find_all("h1", attrs = {"class" : "banner-title"}):
                #print("title gets updated here")
                title = heading.get_text()
                # print(title)
        
        test_x = loaded_vect.transform(total_comments)
        test_y = loaded_new_clf.predict(test_x)
        
        for i in test_y:
            if i == labels[1]:
                ncount += 1
            else:
                pcount += 1        
        
        stored_courses['courses'].append({"name" : course_name, "title" : title, "pcount" : pcount, "ncount" : ncount, "last_updated" : date.today().isoformat()})
        
        with open("course_details.json", "w") as f:
            json.dump(stored_courses, f)

            
    values = [pcount, ncount]
            
    return render_template("predictions.html", values = values, labels = labels, title = title)


if __name__ == "__main__":
    app.run(debug=True)
    