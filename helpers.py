from cs50 import SQL
from flask_uploads import UploadSet, configure_uploads
import csv
import urllib.request
from passlib.context import CryptContext
from passlib.apps import custom_app_context as pwd_context
from flask import redirect, render_template, request, session
from functools import wraps
import os

db = SQL("sqlite:///trigger.db")

def apology(message, code=400):
    """Renders message as an apology to user."""

    def escape(s):
        """ Escape special characters
        https://github.com/jacebrowning/memegen#special-characters """

        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:

            s = s.replace(old, new)

        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Zorgt dat er altijd ingelogd moet zijn.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login(username,password):
    """Inloggen."""

    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

    if len(rows) != 1 or not pwd_context.verify(password, rows[0]["hash"]):
        return apology("invalid username and/or password")

    session["user_id"] = rows[0]["id"]

def home():
    """Homepagina."""

    uploads = db.execute("SELECT gallery.photo_id,photo_description, photo_date, photo_name, username, photo_user_id FROM gallery \
            JOIN users ON photo_user_id = users.id ORDER BY photo_date DESC;")

    for up in uploads:

        trigs = db.execute("SELECT COUNT(*) AS 'trigs' FROM triggers WHERE photo_id = :photo_id LIMIT 1;",
                           photo_id=up['photo_id'])
        up['trigs'] = trigs[0]['trigs']
        comments = db.execute("SELECT username, photo_comment FROM comments JOIN users ON users.id = comments.user_id \
                              WHERE photo_id = :photo_id LIMIT 10", photo_id=up['photo_id'])
        up['comments'] = comments

    return uploads

def upload(filename, photo_description, user_id):
    """Uploaden van foto's."""

    db.execute("INSERT INTO gallery (photo_name, photo_user_id, photo_description) VALUES (:photo_name, :photo_user_id, :photo_description);", \
            photo_name = filename, photo_user_id = user_id, photo_description = photo_description)

def register(username,hash):
    """Registreren van gebruiker"""

    result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)
    if not result:
            return apology("username already taken")

    user_id = db.execute("SELECT id FROM users WHERE username IS :username", \
        username=username)

    session['user_id'] = user_id[0]['id']

def follow(follow_id, user_id):
    """Volgen van gebruiker."""

    db.execute("INSERT INTO volgen (user_id, follower_id) VALUES (:user_id, :follower_id)", user_id = session["user_id"], follower_id = follow_id)

def trigg(photo_id, user_id):
    """Triggen van een foto."""

    db.execute("INSERT INTO triggers (user_id, photo_id) VALUES (:user_id, :photo_id)", user_id = user_id, photo_id = photo_id)

def getrigged():
    """Getriggerde foto's."""

    getrigged = db.execute("SELECT photo_id FROM triggers WHERE user_id = :user_id", user_id=session["user_id"])

    triggs = []
    for trig in getrigged:
        triggs.append(trig['photo_id'])

    return triggs

def comment(photo_comment, photo_id):
    """Reageren onder foto's."""

    comment = db.execute("INSERT INTO comments (photo_comment, user_id, photo_id ) VALUES (:photo_comment, :user_id, :photo_id);", \
    photo_comment = photo_comment, user_id = session["user_id"], photo_id = photo_id)

    return comment

def volgend():
    """Gevolgde gebruikers."""

    volgend = db.execute("SELECT follower_id FROM volgen WHERE user_id = :user_id", user_id=session["user_id"])

    volgers = []
    for volg in volgend:
        volgers.append(volg['follower_id'])

    return volgers

def key():
    """API_KEY."""

    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")

    return key

def gif(filename):
    """Slaat gif op."""

    db.execute("INSERT INTO gallery (photo_name, photo_user_id) VALUES (:photo_name, :photo_user_id);", \
            photo_name = filename, photo_user_id = session["user_id"])

def volgend_feed(volgend):
    """Alle gebruikers die gevolgd worden."""

    uploads = db.execute("SELECT gallery.photo_id,photo_description, photo_date, photo_name, username, photo_user_id FROM gallery \
           JOIN users ON photo_user_id = users.id WHERE photo_user_id IN (:volgend) ORDER BY photo_date DESC;", volgend= volgend);

    for up in uploads:
        trigs = db.execute("SELECT COUNT(*) AS 'trigs' FROM triggers WHERE photo_id = :photo_id LIMIT 1;", photo_id=up['photo_id'])
        up['trigs'] = trigs[0]['trigs']
        comments = db.execute("SELECT username, photo_comment FROM comments JOIN users ON users.id = comments.user_id \
                             WHERE photo_id = :photo_id LIMIT 10", photo_id=up['photo_id'])
        up['comments'] = comments

    return uploads

def current_user():
    """De gebruiker op dat moment."""

    userpage = db.execute("SELECT photo_user_id FROM gallery WHERE photo_user_id = :user_id", user_id=session["user_id"])

    user = []
    for us in userpage:
        user.append(us['photo_user_id'])

    return user

def profile_feed(user):
    """Profiel van de gebruiker."""

    uploads = db.execute("SELECT gallery.photo_id,photo_description, photo_date, photo_name, username, photo_user_id FROM gallery \
            JOIN users ON photo_user_id = users.id WHERE photo_user_id IN (:user) ORDER BY photo_date DESC;", user=user);

    for up in uploads:
        trigs = db.execute("SELECT COUNT(*) AS 'trigs' FROM triggers WHERE photo_id = :photo_id LIMIT 1;",
                          photo_id=up['photo_id'])
        up['trigs'] = trigs[0]['trigs']
        comments = db.execute("SELECT username, photo_comment FROM comments JOIN users ON users.id = comments.user_id \
                             WHERE photo_id = :photo_id LIMIT 10", photo_id=up['photo_id'])
        up['comments'] = comments

    return uploads

def new_password():
    """Wachtwoord veranderen."""

    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])

    if len(rows) != 1  or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
        return apology("Wachtwoord klopt niet.")

    db.execute("UPDATE users SET hash = :hash WHERE id = :user_id",\
            hash = pwd_context.hash(request.form.get("new-password")),\
            user_id = session["user_id"])

    return new_password