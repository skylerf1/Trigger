from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.context import CryptContext
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, render_template, request
from flask_uploads import UploadSet, configure_uploads, IMAGES
myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt"])
from tempfile import mkdtemp
import time
import giphy_client
from giphy_client.rest import ApiException
from operator import itemgetter
import json
import os
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

@app.route("/", methods=['GET', 'POST'])
@helpers.login_required
def homepage():
    if request.method == "GET":

        uploads = helpers.home()
        volgend = helpers.volgend()
        getrigged = helpers.getrigged()

        if not uploads:
            return helpers.apology("Geen foto's beschikbaar.")

        return render_template("homepage.html", uploads = uploads, volgend=volgend, getrigged = getrigged)

    return render_template('homepage.html')

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

    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return helpers.apology("must provide username")

        elif not password:
            return helpers.apology("must provide password")

        helpers.login(username, password)

        return redirect(url_for("homepage"))

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    session.clear()

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmpassword")

        if not username:
            return helpers.apology("Missing username!")

        elif not password:
            return helpers.apology("must provide password!")

        elif not password == confirmation:
            return helpers.apology("passwords do not match")

        hash = myctx.hash(password)

        helpers.register(username,hash)

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

    if request.method == 'POST':

        if not request.form.get('password'):
            return helpers.apology("Voer je oude wachtwoord in.")

        rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session['user_id'])

        if len(rows) != 1 or not pwd_context.verify(request.form.get('password'), rows[0]['hash']):
            return helpers.apology("old password invalid")

        if not request.form.get("new-password"):
            return helpers.apology("must provide new password")

        if not request.form.get("password-confirm"):
            return helpers.apology("must provide password confirmation")

        if request.form.get("new-password") != request.form.get("password-confirm"):
            return helpers.apology("passwords must match")

        password = request.form.get("new-password")
        hash = myctx.hash(password)

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

@app.route('/comment/<picid>', methods=['GET','POST'])
@helpers.login_required
def comment(picid):
        if request.method == 'POST' and request.form.get("inputcomment") != None:

            photo_id = picid
            photo_comment = request.form.get("inputcomment")
            helpers.comment(photo_comment, photo_id)

            return redirect(url_for("homepage"))

        return render_template('comment.html', picid = picid)

@app.route("/gifsearch", methods=["GET", "POST"])
@helpers.login_required
def gifsearch():
    if request.method == "POST":

        gifsearch = request.form.get("searchgif")
        helpers.key()
        api_key = os.environ.get("API_KEY")
        api_instance = giphy_client.DefaultApi()
        q = gifsearch
        limit = 21
        offset = 0
        lang = 'en'

        try:
            api_response = api_instance.gifs_search_get(api_key, q, limit=limit, offset=offset, lang = lang)
            return render_template("gif.html", api_response=api_response)

        except ApiException as e:
            return apology ("Sorry, no gifs found")

    else:
        return render_template("gifsearch.html")

@app.route("/savegif", methods=["GET", "POST"])
@helpers.login_required
def savegif():
    if request.method == "POST":
        return redirect(url_for("upload"))

    else:
        filename = request.args.get('url')
        helpers.giphy(filename)
        return redirect(url_for("homepage"))

@app.route("/getgif/<gifje>", methods=["GET"])
def getgif(gifje):
    return redirect("https://media1.giphy.com/media/" + gifje+"/giphy.gif")

@app.route("/follower_feed", methods=['GET', 'POST'])
@helpers.login_required
def follower_feed():
    if request.method == "GET":
        volgend = helpers.volgend()
        uploads = helpers.volgend_feed(volgend)

        if not uploads:
            return helpers.apology("Geen foto's beschikbaar.")

        return render_template("follower_feed.html", uploads=uploads, volgend=volgend)

    else:
        return render_template("follower_feed.html")

@app.route("/profile", methods=['GET', 'POST'])
@helpers.login_required
def profile():
    if request.method == "GET":
        user = helpers.current_user()
        uploads = helpers.profile_feed(user)
        volgend = helpers.volgend()

        if not uploads:
            return helpers.apology("Geen foto's beschikbaar.")

        return render_template("profile.html", user=user, uploads=uploads, volgend=volgend)

    else:
        return render_template("profile.html")