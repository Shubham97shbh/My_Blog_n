from flask import Flask, render_template,request
from flask_sqlalchemy import SQLAlchemy
import smtplib
from bs4 import BeautifulSoup
import lxml

import requests

Email = "smtp.check.shubham@gmail.com"
password = "$hubham97$"

API_key = "998bc32112ed449086e353dd85a08119"
URL_new = "https://newsapi.org/v2/everything"
param = {'q': 'cryptocurrency world', 'language': 'en', 'sortBy': 'publishedAt',
         'apiKey': '998bc32112ed449086e353dd85a08119'}


class new:
    def __init__(self):
        self.news_update = {}


def requets_data(URL):
    response = requests.get(url=URL)
    soup = BeautifulSoup(response.text, 'lxml')
    content = ''
    for i in soup.find_all('p'):
        if len(i.text) > 35:
            content = content + f" {i.text}"
    return content


news = new()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class news_db(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title= db.Column(db.String(500),unique=True,nullable=False)
    date = db.Column( db.String(20),nullable=False)
    author = db.Column(db.String(30),nullable=True)
    img_url = db.Column(db.String(500),nullable=True)
    subtitle = db.Column(db.String(1000),nullable=True)

db.create_all()

def check_news():
    response = requests.get(url=URL_new, params=param)
    result = (response.json()['articles'])
    db.session.query(news_db).delete()
    db.session.commit()
    for news in result:
       try:
           new_news = news_db(title=news['title'],author=news['author'],date=news['publishedAt'],img_url=news['urlToImage'],subtitle=news['content'])
           db.session.add(new_news)
           db.session.commit()
       except:
           db.session.rollback()
    db.session.commit()
    news_data = news_db.query.all()
    return result

@app.route('/')
def blog():
    return render_template('index.html', value=news.news_update)


@app.route('/index')
def index():
    news.news_update = check_news()
    return render_template('index.html', value=news.news_update)


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/success',methods=['POST','GET'])
def message_me():
    if request.method=='POST':
        name_d = request.form.get('name')
        email_d = request.form.get('email')
        phone_no = request.form.get('phone_no.')
        content = request.form.get('message')
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=Email, password=password)
            connection.sendmail(from_addr=Email, to_addrs="shubham97shbh@gmail.com",
                                msg=f"""Subject:Your friend from blog sent you a message.\n\nHello Shubham!\nMyself {name_d}\n{content}\nPhone No.- {phone_no} and emailID is {email_d}""")

        return render_template('success.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post-<inx>')
def post(inx):
    content = requets_data(news.news_update[int(inx)]['url'])
    return render_template('post.html', value=news.news_update[int(inx)], content=content)


if __name__ == "__main__":
    app.run(debug=True)
