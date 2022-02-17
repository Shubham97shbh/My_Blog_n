from flask import Flask, render_template, url_for, flash, abort, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, Session
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user, login_url
from forms import LoginForm, RegisterForm, CreatePostForm, CommentForm
import smtplib
from flask_gravatar import Gravatar
import os
from bs4 import BeautifulSoup
import lxml

import requests

# when you're using aws their is error in variable detecting
application = Flask(__name__)
app = application
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SECRET_KEY'] = 'Hellobuffalo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Email = "smtp.check.shubham@gmail.com"
password = "Shubham97$"

API_key = "998bc32112ed449086e353dd85a08119"
URL_new = "https://newsapi.org/v2/everything"
param = {'q': 'cryptocurrency world', 'language': 'en', 'sortBy': 'publishedAt',
         'apiKey': 'apikey'}
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, base_url=None)
login_manager = LoginManager()
login_manager.init_app(app)


# Base = automap_base()
# engine = create_engine("sqlite:///news.db")
# Base.prepare(engine,reflect=True)
# # if file is deleted
# if os.path.isfile('news.db') :
#     User = Base.classes.users
#     news_db = Base.classes.News
#     Comment = Base.classes.comments
#
# else:
# data stored for the users
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    # post_id =  db.Column(db.Integer,db.ForeignKey('News.id'))
    # comments_id = db.Column(db.Integer,db.ForeignKey('comments.id'))

    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    # relationship is taking class and variable
    posts = relationship('news_db', back_populates='client')
    comments = relationship('Comment', back_populates='comment_author')


class news_db(db.Model):
    __tablename__ = 'News'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    client = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='parent_post')
    title = db.Column(db.String(500), unique=True, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(30), nullable=True)
    img_url = db.Column(db.String(500), nullable=True)
    subtitle = db.Column(db.String(1000), nullable=True)


# data from comments for a unique id
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('News.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_post = relationship('news_db', back_populates='comments')
    comment_author = relationship('User', back_populates='comments')
    text = db.Column(db.Text, nullable=False)


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class new:
    def __init__(self):
        self.news_update = {}


news = new()


def request_data(URL):
    response = requests.get(url=URL)
    soup = BeautifulSoup(response.text, 'lxml')
    content = ''
    for i in soup.find_all('p'):
        if len(i.text) > 35:
            content = content + f" {i.text}"
    return content


def check_news():
    response = requests.get(url=URL_new, params=param)
    result = (response.json()['articles'])
    # db.session.query(news_db).delete()
    # db.session.commit()
    for news in result:
        try:
            new_news = news_db(title=news['title'], author=news['author'], date=news['publishedAt']
                               , img_url=news['urlToImage'], subtitle=news['content'])
            db.session.add(new_news)
            db.session.commit()
        except:
            db.session.rollback()
    db.session.commit()
    news_db.query.all()
    return result


@app.route('/')
def blog():
    logout()
    news.news_update = check_news()
    return render_template('index.html', current_user=current_user, value=news.news_update)


@app.route('/index')
def index():
    news.news_update = check_news()
    return render_template('index.html', current_user=current_user, value=news.news_update)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/success', methods=['POST', 'GET'])
def message_me():
    if request.method == 'POST':
        name_d = request.form.get('name')
        email_d = request.form.get('email')
        phone_no = request.form.get('phone_no.')
        content = request.form.get('message')
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=Email, password=password)
            connection.sendmail(from_addr=Email, to_addrs="shubham97shbh@gmail.com",
                                msg=f"""Subject:Your friend from blog sent you a message.\n\nHello Shubham!\nMyself {name_d}\n{content}\nYou can contact me on Phone No.- {phone_no} and emailID is {email_d}""")

        return render_template('success.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post-<inx>')
def show_post(inx):
    content = request_data(news.news_update[int(inx)]['url'])
    return render_template('post.html', value=news.news_update[int(inx)], current_user=current_user, content=content)


@app.route("/post/<int:inx>", methods=["GET", "POST"])
def post(inx):
    form = CommentForm()
    requested_post = news_db.query.get(inx)
    content = request_data(news.news_update[int(inx)]['url'])
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', inx=inx))

    return render_template("post.html", content=content, post=requested_post, form=form, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("you've already signed up with that email,try another email")
            return redirect(url_for('login'))
        new_user = User(email=form.email.data, name=form.name.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('post'))

    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('That email does not exist, please try again')
            return redirect(url_for('login'))
        elif password != user.password:
            flash('Password incorrect,please try again')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
