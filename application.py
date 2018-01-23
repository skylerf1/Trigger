from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.context import CryptContext
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES
myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt"])
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///trigger.db")

@app.route("/")
@login_required
def homepage():
    if request.method == "GET":
        uploads = db.execute("SELECT * FROM gallery")

        return render_template("homepage.html", uploads = uploads)


photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])

        photo_description = (request.form.get("inputDescription"))
        # photo_name = (request.form.get("file"))

        db.execute("INSERT INTO gallery (photo_name, photo_user_id, photo_description) VALUES (:photo_name, :photo_user_id, :photo_description);", \
            photo_name = filename, photo_user_id = session["user_id"], photo_description = photo_description)

        return redirect(url_for("homepage"))
    return render_template('upload.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("homepage"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

# @app.route("/homepage", methods=["GET", "POST"])
# @login_required
# def quote():
#     """Get stock quote."""
#     return apology("TODO lollll")

@app.route("/register", methods=["GET", "POST"])
def register():
    # forget any user_id
    session.clear()

    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username!")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password!")

        elif not request.form.get("password") == request.form.get("confirmpassword"):
            return apology("passwords do not match")

        # change to hash for security
        hash = myctx.hash(request.form.get("password"))

        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
            username=request.form.get("username"), hash=hash)
        print (result)
        if not result:
            return apology("username already taken")

        user_id = db.execute("SELECT id FROM users WHERE username IS :username",\
        username=request.form.get("username"))


        # remember which user has logged in
        session['user_id'] = user_id[0]['id']

        # redirect user to home page
        return redirect(url_for("homepage"))
    else:
        return render_template("register.html")
