from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
 
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
            status TEXT DEFAULT 'wil spelen',
            user_rating INTEGER DEFAULT NULL
        );
 
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_title TEXT NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            review TEXT NOT NULL,
            datum TEXT DEFAULT (date('now'))
        );
    """)
    # user_rating kolom toevoegen als die nog niet bestaat (voor bestaande databases)
    try:
        conn.execute("ALTER TABLE games ADD COLUMN user_rating INTEGER DEFAULT NULL")
        conn.commit()
    except:
        pass
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
    return render_template("index.html", games=games, current_user=session["user"])
 
 
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
 
 
# --- API: genres ophalen voor een game ---
@app.route("/get_genres")
def get_genres():
    name = request.args.get("name", "")
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    genres = games_conn.execute(
        "SELECT gr.genre FROM genre gr JOIN game g ON g.id = gr.game_id WHERE g.name = ?",
        (name,)
    ).fetchall()
    games_conn.close()
    return jsonify([row["genre"] for row in genres])
 
 
# --- Game toevoegen ---
@app.route("/add", methods=["GET", "POST"])
def add_game():
    if "user" not in session:
        return redirect(url_for("login"))
 
    if request.method == "POST":
        title = request.form["title"].strip()
        genre = request.form.get("genre", "").strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]
        user_rating = request.form.get("user_rating") or None
        if user_rating:
            user_rating = int(user_rating)
 
        if not title:
            flash("Titel is verplicht.", "danger")
            return redirect(url_for("add_game"))
 
        conn = get_db()
        conn.execute(
            "INSERT INTO games (title, genre, platform, added_by, status, user_rating) VALUES (?, ?, ?, ?, ?, ?)",
            (title, genre, platform, session["user"], status, user_rating),
        )
        conn.commit()
        conn.close()
        flash(f'"{title}" toegevoegd aan de wishlist!', "success")
        return redirect(url_for("index"))
 
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
 
    if game["added_by"] != session["user"]:
        conn.close()
        flash("Je kan alleen je eigen games bewerken.", "danger")
        return redirect(url_for("index"))
 
    if request.method == "POST":
        title = request.form["title"].strip()
        genre = request.form.get("genre", "").strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]
        user_rating = request.form.get("user_rating") or None
        if user_rating:
            user_rating = int(user_rating)
 
        conn.execute(
            "UPDATE games SET title = ?, genre = ?, platform = ?, status = ?, user_rating = ? WHERE id = ?",
            (title, genre, platform, status, user_rating, game_id),
        )
        conn.commit()
        conn.close()
        flash("Game bijgewerkt!", "success")
        return redirect(url_for("index"))
 
    conn.close()
 
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()
 
    return render_template("edit_game.html", game=game, alle_games=alle_games)
 
 
# --- Game verwijderen ---
@app.route("/delete/<int:game_id>")
def delete_game(game_id):
    if "user" not in session:
        return redirect(url_for("login"))
 
    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
 
    if not game:
        conn.close()
        flash("Game niet gevonden.", "danger")
        return redirect(url_for("index"))
 
    if game["added_by"] != session["user"]:
        conn.close()
        flash("Je kan alleen je eigen games verwijderen.", "danger")
        return redirect(url_for("index"))
 
    conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    flash("Game verwijderd.", "info")
    return redirect(url_for("index"))
 
 
# --- Reviews pagina ---
@app.route("/reviews")
def reviews():
    if "user" not in session:
        return redirect(url_for("login"))
 
    conn = get_db()
    alle_reviews = conn.execute(
        "SELECT * FROM reviews ORDER BY datum DESC, id DESC"
    ).fetchall()
    conn.close()
 
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()
 
    return render_template("reviews.html", reviews=alle_reviews, alle_games=alle_games)
 
 
# --- Review toevoegen ---
@app.route("/reviews/add", methods=["POST"])
def add_review():
    if "user" not in session:
        return redirect(url_for("login"))
 
    game_title = request.form["game_title"].strip()
    rating = request.form.get("rating") or None
    review = request.form["review"].strip()
 
    if not game_title or not review or not rating:
        flash("Vul alle velden in.", "danger")
        return redirect(url_for("reviews"))
 
    conn = get_db()
    conn.execute(
        "INSERT INTO reviews (game_title, username, rating, review) VALUES (?, ?, ?, ?)",
        (game_title, session["user"], int(rating), review)
    )
    conn.commit()
    conn.close()
    flash("Review toegevoegd!", "success")
    return redirect(url_for("reviews"))
 
 
# --- Review verwijderen ---
@app.route("/reviews/delete/<int:review_id>")
def delete_review(review_id):
    if "user" not in session:
        return redirect(url_for("login"))
 
    conn = get_db()
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
 
    if not review or review["username"] != session["user"]:
        conn.close()
        flash("Je kan alleen je eigen reviews verwijderen.", "danger")
        return redirect(url_for("reviews"))
 
    conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review verwijderd.", "info")
    return redirect(url_for("reviews"))
 
 
if __name__ == "__main__":
    init_db()
    app.run(debug=True)