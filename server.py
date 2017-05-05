"""Movie Ratings."""

from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from flask import (Flask, render_template, redirect, request, flash,
                   session)
from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route("/movies")
def movie_list():
    """Show list of movies."""
    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movie_list.html", movies=movies)

@app.route('/create-account', methods=['GET'])
def create_account():
    """ Allows user to create a new account """
    return render_template('create_account.html')


@app.route('/create-account', methods=['POST'])
def check_create():
    """ Checks user email is new and processes registration """
    
    user_email = request.form.get('email')
    print user_email
    user_password = request.form.get('password')
    user_age = request.form.get('age')
    user_zip = request.form.get('zip_code')
    print "Got here!"

    user = User.query.filter_by(email=user_email).all()
    print user

    if user:
        flash("User email already exists")
        return redirect('/login-form')
    else:
        new_user = User(email=user_email, password=user_password, age=user_age, zipcode=user_zip)
        db.session.add(new_user)
        db.session.commit()
        session['logged_in_email'] = user_email
        flash('You are now registered and logged in!')
        return redirect('/')


@app.route('/logout')
def logout():
    """Logs out user"""
    del session['logged_in_email']
    flash("You are now logged out.")
    return redirect('/')


@app.route('/login-form')
def login():
    """Prompts user to log in"""

    return render_template('login_form.html')


@app.route('/check-login', methods=['POST'])
def check_login():
    """Check if email in users table"""
    # TODO: check email address against database
    user_email = request.form.get('email')
    user_password = request.form.get('password')

    try:
        user = User.query.filter_by(email=user_email).one()
        if user.password == user_password:
            session['logged_in_email'] = user_email
            flash('You are now logged in!')
            return redirect('/users/%s' % (user.user_id))
        else:
            flash('Wrong password!')
            return redirect('/login-form')

    except:
        flash("No user with that email")
        return redirect('/create-account')

@app.route('/users/<user_id>')
def user_profile(user_id):
    """Displays a user's profile """
    user = User.query.get(user_id)
    user_age = user.age
    user_zip = user.zipcode
    ratings = user.ratings

    user_ratings = []
    for rating in ratings:
        user_ratings.append((rating.movie.title, rating.score))

    return render_template('user_profile.html', user_age=user_age, user_zip=user_zip,
                            user_ratings=user_ratings)


@app.route('/movies/<movie_id>')
def movie_profile(movie_id):
    """Displays a movie's profile """
    movie = Movie.query.get(movie_id)
    movie_title = movie.title
    movie_date = movie.released_at
    movie_url = movie.imdb_url
    ratings = movie.ratings

    scores = []
    user_rating = None
    prediction = None

    for rating in ratings:
        scores.append(rating.score)
    avg = sum(scores) / len(scores)

    if session['logged_in_email']:
        current_user = User.query.filter_by(email=session['logged_in_email']).first()
        try:
            user_rating = Rating.query.filter_by(user_id = current_user.user_id, movie_id = movie_id).first().score
        except:
            user_rating = 0
            prediction = current_user.predict_rating(movie)


    return render_template('movie_profile.html', movie_title=movie_title, movie_date=movie_date,
                            movie_url=movie_url, ratings=scores, avg=avg, user_rating=user_rating, 
                            movie_id=movie_id, prediction=prediction)


@app.route("/rate-movie/<movie_id>", methods=['GET'])
def rate_movie(movie_id):
    """ Rate or update rating for a movie """
    movie = Movie.query.get(movie_id)
    return render_template("rate_movie.html", movie=movie)


@app.route("/rate-movie/<movie_id>", methods=['POST'])
def accept_movie_rating(movie_id):
    """ Change rating of movie for user """

    try:
        current_user = User.query.filter_by(email=session['logged_in_email']).first()
        user_rating = Rating.query.filter_by(user_id=current_user.user_id, movie_id=movie_id).first()
    except:
        user_rating = 0

    movie_rating = request.form.get("movierating")

    if user_rating:
        user_rating.score = movie_rating
    else:
        db.session.add(Rating(movie_id=movie_id, user_id=current_user.user_id, score=movie_rating))

    db.session.commit()

    return redirect('/movies/'+movie_id)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
