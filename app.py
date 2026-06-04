"""
app.py - De hoofdapplicatie voor de Game Wishlist website
=========================================================
Dit bestand bevat alle routes (URL's) en logica van de website.
Flask wordt gebruikt als webframework.

Structuur:
  - Databasefuncties (verbinding maken, aanmaken)
  - RAWG API (gamecovers ophalen)
  - Routes: home, login, register, logout
  - Routes: wishlist (alleen jouw eigen games)
  - Routes: reviews (voor iedereen zichtbaar)
  - Routes: admin paneel
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import urllib.request
import urllib.parse
import json

# ──────────────────────────────────────────────
# App-configuratie
# ──────────────────────────────────────────────

app = Flask(__name__)

# Geheime sleutel voor sessies (verander dit in productie!)
app.secret_key = "verander_dit_later"

# Naam van de SQLite-database voor gebruikers, wishlist en reviews
DATABASE = "wishlist.db"

# API-sleutel voor RAWG (gratis gameplatform voor covers)
RAWG_KEY = "b324b0885e0f498a8d280f7ef35c8669"


# ──────────────────────────────────────────────
# Databasehulpfuncties
# ──────────────────────────────────────────────

def get_db():
    """
    Maakt een verbinding met de wishlist-database.
    row_factory = sqlite3.Row zorgt dat je kolomnamen kunt gebruiken
    als sleutels (bijv. game["title"] in plaats van game[1]).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Maakt alle tabellen aan als ze nog niet bestaan.
    Wordt automatisch uitgevoerd bij het starten van de app.

    Tabellen:
      - users    : alle geregistreerde gebruikers
      - games    : de persoonlijke wishlist-entries (per gebruiker)
      - reviews  : openbare reviews van games
    """
    conn = get_db()
    conn.executescript("""
        -- Gebruikerstabel: bewaart accounts
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0   -- 1 = admin, 0 = gewone gebruiker
        );

        -- Wishlist-tabel: elke rij is een game die iemand heeft toegevoegd
        -- Belangrijk: added_by koppelt een game aan een specifieke gebruiker
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            platform TEXT,
            added_by TEXT NOT NULL,       -- gebruikersnaam van de eigenaar
            status TEXT DEFAULT 'wil spelen',
            user_rating INTEGER DEFAULT NULL
        );

        -- Reviews-tabel: openbare reviews, zichtbaar voor iedereen
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_title TEXT NOT NULL,
            username TEXT NOT NULL,       -- wie de review schreef
            rating INTEGER NOT NULL,
            review TEXT NOT NULL,
            cover_url TEXT,               -- URL van de gamecover (via RAWG API)
            datum TEXT DEFAULT (date('now'))
        );
    """)

    # Kolommen toevoegen als ze nog niet bestaan (bij updates van de app)
    # Try/except vermijdt fouten als de kolom al bestaat
    for sql in [
        "ALTER TABLE games ADD COLUMN user_rating INTEGER DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0",
        "ALTER TABLE reviews ADD COLUMN cover_url TEXT",
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except:
            pass  # Kolom bestaat al, geen actie nodig

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Hulpfuncties
# ──────────────────────────────────────────────

def get_game_cover(game_title):
    """
    Zoekt een gamecover op via de RAWG API.
    Geeft de URL van de afbeelding terug, of None als er niets gevonden wordt.

    Parameters:
        game_title (str): De naam van de game om te zoeken

    Returns:
        str | None: URL naar de coverafbeelding, of None bij fout/geen resultaat
    """
    try:
        # Zet de gamtitel om naar een URL-veilige string (bijv. spaties → %20)
        query = urllib.parse.quote(game_title)
        url = f"https://api.rawg.io/api/games?key={RAWG_KEY}&search={query}&page_size=1"

        # Stuur een verzoek naar de RAWG API
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            results = data.get("results", [])
            if results:
                return results[0].get("background_image")  # URL van de cover
    except:
        pass  # Bij een fout (geen internet, timeout, ...) gewoon None teruggeven
    return None


def is_admin():
    """
    Controleert of de huidige ingelogde gebruiker een admin is.

    Returns:
        bool: True als admin, False als niet ingelogd of geen admin
    """
    if "user" not in session:
        return False
    conn = get_db()
    user = conn.execute(
        "SELECT is_admin FROM users WHERE username = ?", (session["user"],)
    ).fetchone()
    conn.close()
    return user and user["is_admin"] == 1


# ──────────────────────────────────────────────
# Route: Startpagina (home)
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """
    Toont de startpagina/homepagina van de website.
    Als de gebruiker niet ingelogd is, wordt hij doorgestuurd naar login.
    De homepagina is een welkomstscherm met knoppen naar de wishlist en reviews.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    # Geef de gebruikersnaam en adminrol mee aan de template
    return render_template("index.html", current_user=session["user"], admin=is_admin())


# ──────────────────────────────────────────────
# Route: Persoonlijke Wishlist
# ──────────────────────────────────────────────

@app.route("/wishlist")
def wishlist():
    """
    Toont de publieke wishlist met games van ALLE gebruikers.
    Iedereen kan alle toegevoegde games zien.
    Bewerken/verwijderen kan alleen door de eigenaar of een admin.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    # Geen filter op added_by → alle games van alle gebruikers
    games = conn.execute(
        "SELECT * FROM games ORDER BY title"
    ).fetchall()
    conn.close()

    return render_template("wishlist.html", games=games, current_user=session["user"], admin=is_admin())


# ──────────────────────────────────────────────
# Route: Registreren
# ──────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Toont het registratieformulier (GET) en verwerkt het (POST).
    Controleert of de gebruikersnaam al bestaat.
    Slaat het wachtwoord op in plaintext (voor productie: gebruik hashing!).
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # Validatie: beide velden moeten ingevuld zijn
        if not username or not password:
            flash("Vul alle velden in.", "danger")
            return render_template("register.html")

        conn = get_db()
        # Kijk of de gebruikersnaam al bestaat
        bestaand = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if bestaand:
            flash("Gebruikersnaam is al bezet.", "danger")
            conn.close()
            return render_template("register.html")

        # Nieuwe gebruiker aanmaken
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
        )
        conn.commit()
        conn.close()
        flash("Account aangemaakt! Je kan nu inloggen.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ──────────────────────────────────────────────
# Route: Inloggen
# ──────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Toont het loginformulier (GET) en controleert de inloggegevens (POST).
    Bij succes wordt de gebruikersnaam opgeslagen in de sessie.
    De sessie blijft actief totdat de gebruiker uitlogt.
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        # Zoek een gebruiker met de juiste naam én wachtwoord
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username  # Sla gebruikersnaam op in sessie
            return redirect(url_for("index"))
        else:
            flash("Fout gebruikersnaam of wachtwoord.", "danger")

    return render_template("login.html")


# ──────────────────────────────────────────────
# Route: Uitloggen
# ──────────────────────────────────────────────

@app.route("/logout")
def logout():
    """
    Verwijdert de gebruiker uit de sessie (= uitloggen).
    Stuurt daarna door naar de loginpagina.
    """
    session.pop("user", None)
    return redirect(url_for("login"))


# ──────────────────────────────────────────────
# Route: API – Genres ophalen voor een game
# ──────────────────────────────────────────────

@app.route("/get_genres")
def get_genres():
    """
    API-endpoint dat genres ophaalt voor een specifieke game uit games.db.
    Wordt aangeroepen via JavaScript (AJAX) op de add/edit pagina's.

    Query parameter:
        name (str): De naam van de game

    Returns:
        JSON-lijst met genres, bijv. ["RPG", "Action"]
    """
    name = request.args.get("name", "")

    # Gebruik de aparte games.db (met 100 games) – niet de wishlist.db
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    genres = games_conn.execute(
        "SELECT gr.genre FROM genre gr JOIN game g ON g.id = gr.game_id WHERE g.name = ?",
        (name,)
    ).fetchall()
    games_conn.close()

    return jsonify([row["genre"] for row in genres])


# ──────────────────────────────────────────────
# Route: Game toevoegen aan wishlist
# ──────────────────────────────────────────────

@app.route("/add", methods=["GET", "POST"])
def add_game():
    """
    Toont het formulier om een game toe te voegen (GET).
    Verwerkt het formulier en slaat de game op in de database (POST).
    De game wordt automatisch gekoppeld aan de ingelogde gebruiker (added_by).
    """
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Haal de formuliergegevens op
        title = request.form["title"].strip()
        genre = request.form.get("genre", "").strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]
        user_rating = request.form.get("user_rating") or None
        if user_rating:
            user_rating = int(user_rating)  # Omzetten naar getal

        # Validatie: titel is verplicht
        if not title:
            flash("Titel is verplicht.", "danger")
            return redirect(url_for("add_game"))

        conn = get_db()
        # Sla de game op met de ingelogde gebruiker als eigenaar
        conn.execute(
            "INSERT INTO games (title, genre, platform, added_by, status, user_rating) VALUES (?, ?, ?, ?, ?, ?)",
            (title, genre, platform, session["user"], status, user_rating),
        )
        conn.commit()
        conn.close()
        flash(f'"{title}" toegevoegd aan je wishlist!', "success")
        return redirect(url_for("wishlist"))

    # Haal alle beschikbare games op uit de referentiedatabase (games.db)
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()

    return render_template("add_game.html", alle_games=alle_games, admin=is_admin())


# ──────────────────────────────────────────────
# Route: Game bewerken
# ──────────────────────────────────────────────

@app.route("/edit/<int:game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    """
    Laat de gebruiker een game in zijn wishlist bewerken.
    Alleen de eigenaar (of een admin) mag de game aanpassen.

    Parameters:
        game_id (int): Het ID van de te bewerken game
    """
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()

    # Bestaat de game?
    if not game:
        conn.close()
        flash("Game niet gevonden.", "danger")
        return redirect(url_for("wishlist"))

    # Mag deze gebruiker de game bewerken? (alleen eigenaar of admin)
    if game["added_by"] != session["user"] and not is_admin():
        conn.close()
        flash("Je kan alleen je eigen games bewerken.", "danger")
        return redirect(url_for("wishlist"))

    if request.method == "POST":
        # Haal de nieuwe waarden op uit het formulier
        title = request.form["title"].strip()
        genre = request.form.get("genre", "").strip()
        platform = request.form["platform"].strip()
        status = request.form["status"]
        user_rating = request.form.get("user_rating") or None
        if user_rating:
            user_rating = int(user_rating)

        # Werk de game bij in de database
        conn.execute(
            "UPDATE games SET title = ?, genre = ?, platform = ?, status = ?, user_rating = ? WHERE id = ?",
            (title, genre, platform, status, user_rating, game_id),
        )
        conn.commit()
        conn.close()
        flash("Game bijgewerkt!", "success")
        return redirect(url_for("wishlist"))

    conn.close()

    # Haal alle beschikbare games op voor het dropdown-menu
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()

    return render_template("edit_game.html", game=game, alle_games=alle_games, admin=is_admin())


# ──────────────────────────────────────────────
# Route: Game verwijderen
# ──────────────────────────────────────────────

@app.route("/delete/<int:game_id>")
def delete_game(game_id):
    """
    Verwijdert een game uit de wishlist.
    Alleen de eigenaar of een admin mag een game verwijderen.

    Parameters:
        game_id (int): Het ID van de te verwijderen game
    """
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()

    if not game:
        conn.close()
        flash("Game niet gevonden.", "danger")
        return redirect(url_for("wishlist"))

    # Toegangscontrole: alleen eigenaar of admin
    if game["added_by"] != session["user"] and not is_admin():
        conn.close()
        flash("Je kan alleen je eigen games verwijderen.", "danger")
        return redirect(url_for("wishlist"))

    conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    flash("Game verwijderd.", "info")
    return redirect(url_for("wishlist"))


# ──────────────────────────────────────────────
# Route: Reviews (openbaar voor iedereen)
# ──────────────────────────────────────────────

@app.route("/reviews")
def reviews():
    """
    Toont alle reviews van alle gebruikers.
    Reviews zijn OPENBAAR: elke ingelogde gebruiker kan ze lezen.
    Ook het formulier om een nieuwe review te schrijven staat hier.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    # Haal alle reviews op, nieuwste eerst
    alle_reviews = conn.execute(
        "SELECT * FROM reviews ORDER BY datum DESC, id DESC"
    ).fetchall()
    conn.close()

    # Haal gamelijst op voor het review-formulier (dropdown)
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    alle_games = games_conn.execute("SELECT name FROM game ORDER BY name").fetchall()
    games_conn.close()

    return render_template(
        "reviews.html",
        reviews=alle_reviews,
        alle_games=alle_games,
        admin=is_admin()
    )


# ──────────────────────────────────────────────
# Route: Review toevoegen
# ──────────────────────────────────────────────

@app.route("/reviews/add", methods=["POST"])
def add_review():
    """
    Verwerkt het formulier voor een nieuwe review.
    Haalt automatisch de gamecover op via de RAWG API.
    Reviews zijn openbaar en zichtbaar voor alle gebruikers.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    game_title = request.form["game_title"].strip()
    rating = request.form.get("rating") or None
    review = request.form["review"].strip()

    # Alle velden zijn verplicht
    if not game_title or not review or not rating:
        flash("Vul alle velden in.", "danger")
        return redirect(url_for("reviews"))

    # Probeer een gamecover te vinden via de RAWG API
    cover_url = get_game_cover(game_title)

    conn = get_db()
    conn.execute(
        "INSERT INTO reviews (game_title, username, rating, review, cover_url) VALUES (?, ?, ?, ?, ?)",
        (game_title, session["user"], int(rating), review, cover_url)
    )
    conn.commit()
    conn.close()
    flash("Review toegevoegd!", "success")
    return redirect(url_for("reviews"))


# ──────────────────────────────────────────────
# Route: Review verwijderen
# ──────────────────────────────────────────────

@app.route("/reviews/delete/<int:review_id>")
def delete_review(review_id):
    """
    Verwijdert een review.
    Alleen de auteur van de review of een admin mag dit doen.

    Parameters:
        review_id (int): Het ID van de te verwijderen review
    """
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()

    # Toegangscontrole: alleen auteur of admin
    if not review or (review["username"] != session["user"] and not is_admin()):
        conn.close()
        flash("Je kan alleen je eigen reviews verwijderen.", "danger")
        return redirect(url_for("reviews"))

    conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review verwijderd.", "info")
    return redirect(url_for("reviews"))


# ──────────────────────────────────────────────
# Route: Admin paneel
# ──────────────────────────────────────────────

@app.route("/admin")
def admin():
    """
    Toont het admin paneel met een overzicht van alle gebruikers.
    Alleen toegankelijk voor admins.
    """
    if not is_admin():
        flash("Geen toegang.", "danger")
        return redirect(url_for("index"))

    conn = get_db()
    users = conn.execute(
        "SELECT id, username, is_admin FROM users ORDER BY username"
    ).fetchall()
    conn.close()
    return render_template("admin.html", users=users, admin=True)


# ──────────────────────────────────────────────
# Route: Admin – Gebruiker verwijderen
# ──────────────────────────────────────────────

@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    """
    Verwijdert een gebruiker én al zijn games en reviews.
    Alleen admins kunnen dit doen.
    Een admin kan zichzelf niet verwijderen.

    Parameters:
        user_id (int): Het ID van de te verwijderen gebruiker
    """
    if not is_admin():
        flash("Geen toegang.", "danger")
        return redirect(url_for("index"))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        conn.close()
        flash("Gebruiker niet gevonden.", "danger")
        return redirect(url_for("admin"))

    # Voorkomen dat een admin zichzelf verwijdert
    if user["username"] == session["user"]:
        conn.close()
        flash("Je kan jezelf niet verwijderen.", "danger")
        return redirect(url_for("admin"))

    # Verwijder de gebruiker én al zijn gekoppelde data
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.execute("DELETE FROM games WHERE added_by = ?", (user["username"],))
    conn.execute("DELETE FROM reviews WHERE username = ?", (user["username"],))
    conn.commit()
    conn.close()
    flash(f'Gebruiker "{user["username"]}" verwijderd.', "info")
    return redirect(url_for("admin"))


# ──────────────────────────────────────────────
# Route: Admin – Admin rechten geven/afnemen
# ──────────────────────────────────────────────

@app.route("/admin/toggle_admin/<int:user_id>")
def toggle_admin(user_id):
    """
    Geeft een gebruiker admin rechten, of neemt ze af (toggle).
    Een admin kan zijn eigen rechten niet afnemen.

    Parameters:
        user_id (int): Het ID van de gebruiker
    """
    if not is_admin():
        flash("Geen toegang.", "danger")
        return redirect(url_for("index"))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user or user["username"] == session["user"]:
        conn.close()
        flash("Niet mogelijk.", "danger")
        return redirect(url_for("admin"))

    # Wissel tussen 0 (geen admin) en 1 (admin)
    nieuw = 0 if user["is_admin"] == 1 else 1
    conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (nieuw, user_id))
    conn.commit()
    conn.close()
    flash(
        f'Admin rechten {"gegeven aan" if nieuw else "afgenomen van"} "{user["username"]}".',
        "success"
    )
    return redirect(url_for("admin"))


# ──────────────────────────────────────────────
# Opstarten
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# Route: Admin account aanmaken (eenmalige setup)
# ──────────────────────────────────────────────

@app.route("/setup_admin")
def setup_admin():
    """
    Maakt automatisch een admin account aan als het nog niet bestaat.
    Gebruikersnaam: admin
    Wachtwoord:     admin123

    Verwijder of beveilig deze route nadat je bent ingelogd!
    Ga naar: http://localhost:5000/setup_admin
    """
    conn = get_db()
    bestaand = conn.execute(
        "SELECT * FROM users WHERE username = 'admin'"
    ).fetchone()

    if bestaand:
        # Account bestaat al → zet is_admin op 1
        conn.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        conn.commit()
        conn.close()
        return "<h2>Admin account bestaat al en heeft nu adminrechten. <a href='/login'>Inloggen</a></h2>"

    # Nieuw admin account aanmaken
    conn.execute(
        "INSERT INTO users (username, password, is_admin) VALUES ('admin', 'admin123', 1)"
    )
    conn.commit()
    conn.close()
    return "<h2>Admin account aangemaakt! Gebruiker: <b>admin</b> | Wachtwoord: <b>admin123</b>. <a href='/login'>Inloggen</a></h2>"


if __name__ == "__main__":
    # Initialiseer de database bij het opstarten
    init_db()
    # Start de ontwikkelserver (debug=True toont foutmeldingen in de browser)
    app.run(debug=True)
