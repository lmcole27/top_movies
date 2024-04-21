from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

#API INFO
API_KEY = os.environ['API_KEY']
API_AUTHORIZATION = os.environ['API_AUTHORIZATION']
HEADER = headers = {
    "accept": "application/json",
    "Authorization": API_AUTHORIZATION
}

#API URL INFO
search_url = "https://api.themoviedb.org/3/search/movie"   
detail_url = "https://api.themoviedb.org/3/movie/"
poster_url = "https://image.tmdb.org/t/p/w500/"

#CREATE WEB APP
app = Flask(__name__)
SECRET_KEY = os.environ["SECRET_KEY_APP_CONFIG"]
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)

#CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
db = SQLAlchemy()
db.init_app(app)


#CREATE DB TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title  = db.Column(db.String, unique=True, nullable=False)
    year  = db.Column(db.String, nullable=False)
    description  = db.Column(db.String, nullable=False)
    rating  = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String)
    img_url = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()

#FLASK FORMS - WTF
class MyForm(FlaskForm):
    your_rating = StringField('Rating', validators=[DataRequired()])
    your_review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')

class addForm(FlaskForm):
    name = StringField('Movie Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route("/")
def home():

    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()

    for i in range(len(movies)):
        #movies[i].ranking = len(movies) - i
        movies[i].ranking = i + 1
        db.session.commit()    
    return render_template("index.html", movies=movies)

@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = addForm()
    if request.method == "POST":
        movie_title = str(request.form["name"])
        return redirect(url_for("select", title=movie_title))
    return render_template("add.html", form=add_form)

@app.route("/select/<title>", methods=["POST", "GET"])
def select(title):
    response = requests.get(search_url, params={"api_key": API_KEY, "query": title})
    data = response.json()["results"]
    return render_template("select.html", movies=data)

@app.route("/details/<int:movie_id>", methods=["GET", "POST"])
def details(movie_id):
    if request.method == "GET":
        URL = detail_url + str(movie_id)
        response = requests.get(URL, headers=HEADER)
        data = response.json()

        new_movie = Movie(
            title= data["title"],
            year= data["release_date"][0:4],
            description= data["overview"],
            img_url= poster_url + str(data["poster_path"])
            )
    
        with app.app_context():
            db.session.add(new_movie)
            db.session.commit()

        movie_data = db.session.execute(db.select(Movie).where(Movie.title == data["title"])).scalar()        
    return redirect(url_for('edit', id=movie_data.id))

@app.route("/edit/<int:id>", methods=["POST", "GET"])
def edit(id):
    edit_form = MyForm()
    movie_update = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    if request.method == "POST":
        movie_update.rating = request.form["your_rating"]
        movie_update.review = request.form["your_review"]
        db.session.commit()
        return redirect('/')
    return render_template("edit.html", id=id, movie=movie_update, form=edit_form)

@app.route("/delete/<int:id>")
def delete(id):
    movie_delete = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(movie_delete)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
