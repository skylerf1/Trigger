from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
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
    return apology("TODO")

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

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # Zorgt ervoor dat andere gebruikers vergeten worden.
    session.clear()

    if request.method == "POST":

        # Bij het registreren moet een username worden gekozen, anders volgt een errorbericht.
        if not request.form.get("username"):
            return apology("Vul een username in, anders kun je geen account aanmaken!")

        # Bij het registreren moet een wachtwoord worden gekozen, anders een apology.
        elif not request.form.get("password"):
            return apology("Vul een wachtwoord in, anders kun je geen account aanmaken!")

        # Het wachtwoord moet bevestigd worden.
        elif not request.form.get("password_confirmation"):
            return apology("Vul nogmaals je wachtwoord in, anders kun je geen account aanmaken!")

        # Het wachtwoord en de wachtwoordbevestiging moeten overeenkomen, anders geen account.
        elif request.form.get("password") != request.form.get("password_confirmation"):
            return apology("Je wachtwoorden komen niet overeen, probeer opnieuw!")

        # Slaat gebruiker op.
        users = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=pwd_context.encrypt(request.form.get("password")))

        if not users:
            return apology("Probeer een andere gebruikersnaam.")

        session["user_id"] = users

        return redirect(url_for("homepage"))

    # Via "GET"
    else:
        return render_template("register.html")
