from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.context import CryptContext
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES
myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt"])
from tempfile import mkdtemp

import helpers

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



# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///trigger.db")

photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)

@app.route("/")
@helpers.login_required
def homepage():
    if request.method == "GET":
        uploads = helpers.home()
        if not uploads:
            return helpers.apology("Geen foto's beschikbaar.")

        return render_template("homepage.html", uploads = uploads)
        #return render_template('homepage.html')
@app.route('/upload', methods=['GET', 'POST'])
@helpers.login_required
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])

        photo_description = (request.form.get("inputDescription"))

        helpers.upload(filename, photo_description, session["user_id"])

        return redirect(url_for("homepage"))
    return render_template('upload.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # ensure username wasgit submitted
        if not username:
            return helpers.apology("must provide username")

        # ensure password was submitted
        elif not password:
            return helpers.apology("must provide password")

        helpers.login(username, password)

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
# @helpers.helpers.login_required
# def quote():
#     """Get stock quote."""
#     return helpers.apology("TODO lollll")

@app.route("/register", methods=["GET", "POST"])
def register():
    # forget any user_id
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmpassword")

        # ensure username was submitted
        if not username:
            return helpers.apology("Missing username!")

        # ensure password was submitted
        elif not password:
            return helpers.apology("must provide password!")

        elif not password == confirmation:
            return helpers.apology("passwords do not match")

        # change to hash for security
        hash = myctx.hash(password)

        helpers.register(username,hash)

        # redirect user to home page
        return redirect(url_for("homepage"))
    else:
        return render_template("register.html")
@app.route('/follow', methods=['POST'])
@helpers.login_required
def follow():
    if request.form.get("follow"):
        follow_id = request.form.get("follow")
        helpers.follow(follow_id, session["user_id"])

    return redirect(url_for("homepage"))

@app.route('/trigg', methods=['POST'])
@helpers.login_required
def trigg():
    if request.form.get("trigg"):
        photo_id = request.form.get("trigg")

        helpers.trigg(photo_id, session["user_id"])


    return redirect(url_for("homepage"))
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    """Change user password"""
    # manipulate the information the user has submitted
    if request.method == 'POST':

        # ensure old password was submitted
        if not request.form.get('password'):
            return helpers.apology("Voer je oude wachtwoord in.")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session['user_id'])

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get('password'), rows[0]['hash']):
            return helpers.apology("old password invalid")

        # ensure new password was submitted
        if not request.form.get("new-password"):
            return helpers.apology("must provide new password")

        # ensure password confirmation was submitted
        if not request.form.get("password-confirm"):
            return helpers.apology("must provide password confirmation")

        # ensure password and confirmation match
        if request.form.get("new-password") != request.form.get("password-confirm"):
            return helpers.apology("passwords must match")

        # store the hash of the password and not the actual password that was typed in
        password = request.form.get("new-password")
        hash = myctx.hash(password)

        # username must be a unique field
        result = db.execute("UPDATE users SET hash=:hash", hash=hash)
        if not result:
            return helpers.apology("that didn't work")

        return redirect(url_for("homepage"))

    else:
        return render_template("change_password.html")

@app.route("/change_username", methods=["GET", "POST"])
def change_username():
    """Change username"""
    return helpers.apology("moet nog")

@app.route("/profile", methods=["GET", "POST"])
@helpers.login_required
def profile():
    return helpers.apology("moet nog")

@app.route("/delete_account", methods=["GET", "POST"])
@helpers.login_required
def delete_account():
    return helpers.apology("moet nog")