import sqlite3
import random

# Database aanmaken
conn = sqlite3.connect("/home/claude/games.db")
cur = conn.cursor()

# Tabellen aanmaken
cur.executescript("""
CREATE TABLE IF NOT EXISTS game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platform (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS genre (
    game_id INTEGER NOT NULL,
    genre TEXT NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game(id)
);

CREATE TABLE IF NOT EXISTS rating (
    game_id INTEGER NOT NULL,
    rating REAL NOT NULL,
    votes INTEGER NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game(id)
);

-- Koppeltabel game <-> platform (many-to-many)
CREATE TABLE IF NOT EXISTS game_platform (
    game_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game(id),
    FOREIGN KEY (platform_id) REFERENCES platform(id)
);
""")

# Platforms invoegen
platforms = ["PC", "PlayStation 5", "PlayStation 4", "Xbox Series X", "Xbox One",
             "Nintendo Switch", "Mobile", "PlayStation 3", "Xbox 360", "Wii U"]

for p in platforms:
    cur.execute("INSERT INTO platform (name) VALUES (?)", (p,))

conn.commit()

# 100 games
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

genres_pool = ["Action", "RPG", "Shooter", "Adventure", "Strategy", "Simulation",
               "Horror", "Platformer", "Fighting", "Racing", "Sports", "Puzzle",
               "Survival", "Indie", "Open World", "Stealth", "Roguelite", "MMORPG"]

platform_ids = list(range(1, len(platforms) + 1))

for i, game_name in enumerate(games, start=1):
    cur.execute("INSERT INTO game (name) VALUES (?)", (game_name,))
    game_id = cur.lastrowid

    # 1-3 genres per game
    chosen_genres = random.sample(genres_pool, random.randint(1, 3))
    for g in chosen_genres:
        cur.execute("INSERT INTO genre (game_id, genre) VALUES (?, ?)", (game_id, g))

    # rating tussen 5.0 en 10.0, votes tussen 1000 en 500000
    rating = round(random.uniform(5.0, 10.0), 1)
    votes = random.randint(1000, 500000)
    cur.execute("INSERT INTO rating (game_id, rating, votes) VALUES (?, ?, ?)", (game_id, rating, votes))

    # 1-4 platforms per game
    chosen_platforms = random.sample(platform_ids, random.randint(1, 4))
    for pid in chosen_platforms:
        cur.execute("INSERT INTO game_platform (game_id, platform_id) VALUES (?, ?)", (game_id, pid))

conn.commit()
conn.close()
print("Database aangemaakt: games.db")
print(f"100 games ingevoerd met genres, ratings en platforms!")