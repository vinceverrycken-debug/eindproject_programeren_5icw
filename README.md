Game Wishlist Tracker & Reviews
Een webapplicatie waar gebruikers games bijhouden op een gedeelde wishlist en reviews schrijven.
Live: v1nce.pythonanywhere.com 

Functies

Publieke wishlist met status, platform en rating
Reviews met automatische gamecovers via de RAWG API
Registreren en inloggen met sessies
Admin paneel om gebruikers en content te beheren


Flask · SQLite · Jinja2 · Bootstrap · RAWG API · PythonAnywhere

Opstarten
bashgit clone https://github.com/V1nce/project
cd project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
Ga naar http://localhost:5000 — admin account aanmaken via /setup_admin.

Keuzes

Publieke wishlist — iedereen ziet elkaars games, niet alleen de eigen lijst
RAWG API — gamecovers automatisch ophalen, gebruiker hoeft niets te uploaden
Admin rol — via is_admin in de database, zonder rechtstreeks in de database te gaan


Vince — 5de jaar secundair — Eindproject Programmeren
