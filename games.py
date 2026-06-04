"""
games.py – Referentiedatabase aanmaken
========================================
Dit script maakt een aparte database aan (games.db) met 100 bekende games,
inclusief genres, ratings en platforms. Dit is de REFERENTIEDATABASE:
  - De wishlist-app (app.py) leest hieruit om gamekeuzes aan te bieden
  - Gebruikers voegen games toe aan hun eigen wishlist (wishlist.db)
  - Dit script hoef je maar één keer uit te voeren

Tabellen in games.db:
  - game          : de 100 beschikbare games (id, name)
  - platform      : beschikbare platforms (id, name)
  - genre         : genres per game (game_id, genre)
  - rating        : score en stemmen per game (game_id, rating, votes)
  - game_platform : koppeltabel game ↔ platform (many-to-many)

Gebruik:
  python games.py
"""

import sqlite3
import random

# ──────────────────────────────────────────────
# Database aanmaken / verbinding openen
# ──────────────────────────────────────────────

# Maak verbinding met games.db (wordt aangemaakt als het nog niet bestaat)
conn = sqlite3.connect("/home/claude/games.db")
cur = conn.cursor()


# ──────────────────────────────────────────────
# Tabellen aanmaken
# ──────────────────────────────────────────────

cur.executescript("""
-- Hoofdtabel voor games
CREATE TABLE IF NOT EXISTS game (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Platformtabel (bijv. PC, PS5, Switch)
CREATE TABLE IF NOT EXISTS platform (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Genres per game (een game kan meerdere genres hebben)
CREATE TABLE IF NOT EXISTS genre (
    game_id INTEGER NOT NULL,
    genre   TEXT NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game(id)
);

-- Rating en aantal stemmen per game
CREATE TABLE IF NOT EXISTS rating (
    game_id INTEGER NOT NULL,
    rating  REAL NOT NULL,      -- bijv. 8.5
    votes   INTEGER NOT NULL,   -- aantal stemmen
    FOREIGN KEY (game_id) REFERENCES game(id)
);

-- Koppeltabel: welke game is beschikbaar op welk platform (many-to-many)
-- Een game kan op meerdere platforms staan, een platform heeft meerdere games
CREATE TABLE IF NOT EXISTS game_platform (
    game_id     INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    FOREIGN KEY (game_id)     REFERENCES game(id),
    FOREIGN KEY (platform_id) REFERENCES platform(id)
);
""")


# ──────────────────────────────────────────────
# Platforms invoegen
# ──────────────────────────────────────────────

# Lijst van alle beschikbare platforms
platforms = [
    "PC", "PlayStation 5", "PlayStation 4", "Xbox Series X", "Xbox One",
    "Nintendo Switch", "Mobile", "PlayStation 3", "Xbox 360", "Wii U"
]

# Voeg elk platform in als een rij
for p in platforms:
    cur.execute("INSERT INTO platform (name) VALUES (?)", (p,))

conn.commit()


# ──────────────────────────────────────────────
# Games invoegen (100 stuks)
# ──────────────────────────────────────────────

# Lijst van 100 bekende games
games = [
    "The Legend of Zelda: Breath of the Wild", "Red Dead Redemption 2", "The Witcher 3: Wild Hunt",
    "God of War", "Grand Theft Auto V", "Minecraft", "Dark Souls III", "Elden Ring",
    "Cyberpunk 2077", "Halo Infinite", "Forza Horizon 5", "FIFA 23", "Call of Duty: Warzone",
    "Apex Legends", "Fortnite", "Among Us", "Stardew Valley", "Hollow Knight",
    "Celeste", "Disco Elysium", "Hades", "Death Stranding", "Ghost of Tsushima",
    "Spider-Man: Miles Morales", "Ratchet & Clank: Rift Apart", "Returnal", "Deathloop",
    "It Takes Two", "Resident Evil Village", "Mass Effect Legendary Edition",
    "Final Fantasy XIV", "Monster Hunter: World", "Sekiro: Shadows Die Twice",
    "Persona 5 Royal", "Dragon Age: Inquisition", "The Elder Scrolls V: Skyrim",
    "Fallout 4", "Doom Eternal", "Control", "Outer Wilds", "Subnautica",
    "No Man's Sky", "Valheim", "Rust", "ARK: Survival Evolved", "Terraria",
    "Starbound", "RimWorld", "Factorio", "Satisfactory", "Deep Rock Galactic",
    "Phasmophobia", "Fall Guys", "Rocket League", "Overwatch 2", "Valorant",
    "League of Legends", "Dota 2", "Counter-Strike 2", "Rainbow Six Siege",
    "Battlefield 2042", "Back 4 Blood", "Left 4 Dead 2", "Portal 2",
    "Half-Life: Alyx", "Team Fortress 2", "Titanfall 2", "Doom (2016)",
    "Wolfenstein II: The New Colossus", "Bioshock Infinite", "Dishonored 2",
    "Prey (2017)", "Deus Ex: Mankind Divided", "Hitman 3", "Metal Gear Solid V",
    "Assassin's Creed Valhalla", "Watch Dogs: Legion", "Far Cry 6",
    "Horizon Zero Dawn", "Days Gone", "The Last of Us Part II", "Uncharted 4",
    "Detroit: Become Human", "Heavy Rain", "Beyond: Two Souls", "Death's Door",
    "Spiritfarer", "A Short Hike", "Ori and the Will of the Wisps", "Cuphead",
    "Shovel Knight", "Dead Cells", "Slay the Spire", "Into the Breach",
    "FTL: Faster Than Light", "Divinity: Original Sin 2", "Baldur's Gate 3",
    "Pathfinder: Wrath of the Righteous", "Wasteland 3", "Pillars of Eternity II",
    "Fire Emblem: Three Houses", "XCOM 2", "Total War: Warhammer III",
    "Age of Empires IV", "Civilization VI"
]

# Alle mogelijke genres waaruit willekeurig gekozen wordt
genres_pool = [
    "Action", "RPG", "Shooter", "Adventure", "Strategy", "Simulation",
    "Horror", "Platformer", "Fighting", "Racing", "Sports", "Puzzle",
    "Survival", "Indie", "Open World", "Stealth", "Roguelite", "MMORPG"
]

# Lijst van platform-ID's (1 t/m aantal platforms)
platform_ids = list(range(1, len(platforms) + 1))


# ──────────────────────────────────────────────
# Elke game invullen met genres, rating en platforms
# ──────────────────────────────────────────────

for i, game_name in enumerate(games, start=1):
    # Voeg de game in en haal het automatisch gegenereerde ID op
    cur.execute("INSERT INTO game (name) VALUES (?)", (game_name,))
    game_id = cur.lastrowid

    # Kies willekeurig 1 tot 3 genres voor deze game
    chosen_genres = random.sample(genres_pool, random.randint(1, 3))
    for g in chosen_genres:
        cur.execute(
            "INSERT INTO genre (game_id, genre) VALUES (?, ?)",
            (game_id, g)
        )

    # Genereer een willekeurige rating (5.0–10.0) en aantal stemmen (1000–500000)
    rating = round(random.uniform(5.0, 10.0), 1)
    votes = random.randint(1000, 500000)
    cur.execute(
        "INSERT INTO rating (game_id, rating, votes) VALUES (?, ?, ?)",
        (game_id, rating, votes)
    )

    # Koppel de game aan 1 tot 4 willekeurige platforms
    chosen_platforms = random.sample(platform_ids, random.randint(1, 4))
    for pid in chosen_platforms:
        cur.execute(
            "INSERT INTO game_platform (game_id, platform_id) VALUES (?, ?)",
            (game_id, pid)
        )

# Sla alle wijzigingen op en sluit de verbinding
conn.commit()
conn.close()

print("Database aangemaakt: games.db")
print("100 games ingevoerd met genres, ratings en platforms!")
