from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "verander_dit_later"

DATABASE = "wishlist.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            platform TEXT,
            added_by TEXT NOT NULL,
            status TEXT DEFAULT 'wil spelen'
        );
    """)
    conn.commit()
    conn.close()


# --- Home ---
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    games = conn.execute("SELECT * FROM games ORDER BY title").fetchall()
    conn.close()
    return render_template("index.html", games=games)


# --- Register ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("Vul alle velden in.", "danger")
            return render_template("register.html")

        conn = get_db()
        bestaand = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if bestaand:
            flash("Gebruikersnaam is al bezet.", "danger")
            conn.close()
            return render_template("register.html")

        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash("Account aangemaakt! Je kan nu inloggen.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# --- Login ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            flash("Fout gebruikersnaam of wachtwoord.", "danger")

    return render_template("login.html")


# --- Logout ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# --- Game toevoegen ---
@app.route("/add", methods=["GET", "POST"])
def add_game():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        genre = request.form["genre"].strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]

        if not title:
            flash("Titel is verplicht.", "danger")
            return render_template("add_game.html")

        conn = get_db()
        conn.execute(
            "INSERT INTO games (title, genre, platform, added_by, status) VALUES (?, ?, ?, ?, ?)",
            (title, genre, platform, session["user"], status),
        )
        conn.commit()
        conn.close()
        flash(f'"{title}" toegevoegd aan de wishlist!', "success")
        return redirect(url_for("index"))

    # Games ophalen uit games.db voor de dropdown
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()

    return render_template("add_game.html", alle_games=alle_games)


# --- Game bewerken ---
@app.route("/edit/<int:game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()

    if not game:
        conn.close()
        flash("Game niet gevonden.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"].strip()
        genre = request.form["genre"].strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]

        conn.execute(
            "UPDATE games SET title = ?, genre = ?, platform = ?, status = ? WHERE id = ?",
            (title, genre, platform, status, game_id),
        )
        conn.commit()
        conn.close()
        flash("Game bijgewerkt!", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit_game.html", game=game)


# --- Game verwijderen ---
@app.route("/delete/<int:game_id>")
def delete_game(game_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    flash("Game verwijderd.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
