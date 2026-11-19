# OSINT Investigation Challenge (Fictional)

Two separate-looking websites powered by one Flask app and SQLite database:

- **Company portal** at `/company/` — fictional login and question-based account recovery.
- **Circles profile** at `/social/` — public fictional social profile for Nuyem Limbu.
- **Admin dashboard** at `/admin/` — add/edit/delete questions, posts, friends, comments, profile details; upload images and change branding.

All names, accounts and information are fictional. **No real credentials are collected.** You create all challenge questions, answers and public clues yourself.

## Install (Windows / VS Code)

Open a terminal in the folder containing `app.py`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app create-admin
flask --app app run --debug
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe -m flask --app app ...` for subsequent commands.

Choose your own admin username and **at least 12-character** password when prompted (the input will be hidden). No admin password is supplied or hardcoded.

## Open the sites

- Home: http://127.0.0.1:5000/
- Company: http://127.0.0.1:5000/company/
- Forgotten login: http://127.0.0.1:5000/company/forgot-login
- Public profile: http://127.0.0.1:5000/social/
- Admin: http://127.0.0.1:5000/admin/login

## Populate the challenge

1. Sign in to the admin dashboard.
2. Open **Security questions** and add your questions and the private correct answers. They are hashed and **not sent to public HTML**.
3. Open **Social profile**, **Posts**, **Friends**, and **About fields** and add your own clues. None are automatically generated from answers.
4. Test the challenge in a separate incognito/private window. All security questions must be answered correctly to reach the success page.

The company username/password sign-in is deliberately non-functional in this challenge: it displays a training notice directing participants to the Forgot Login workflow. **Do not enter real credentials.** This isn't a real authentication provider; the account recovery flow is an intentionally solvable puzzle.

## Files

- `app.py` creates Flask app, registers blueprints, includes CLI setup commands and CSRF checks.
- `config.py` has Flask and database settings.
- `models.py` defines SQLite models.
- `extensions.py` initialises Flask-SQLAlchemy and Flask-Login.
- `company/routes.py`, `social/routes.py`, `admin/routes.py` each own their routes.
- `templates/` contains separate Jinja template sets.
- `static/css/` contains separate design themes.
- `uploads/` contains image assets created through admin forms.
- `instance/challenge.db` is created automatically on first launch. You can still run `flask --app app init-db` to add any missing starter records.

## Notes and security

- All user-facing pages have a disclaimer identifying the fictional simulation.
- The protected admin uses Flask-Login and hashed passwords, CSRF form tokens, extension and image-header upload validation, and an 8 MB upload limit. For an internet-facing installation, add request-rate limits, HTTPS, operational monitoring, and stronger image decoding/re-encoding checks.
- Set a strong **SECRET_KEY** in your environment before publishing (not the development fallback). Set `COOKIE_SECURE=1` if serving over HTTPS.
- Never deploy with Flask's debug server or debug mode enabled. Use a production WSGI server and HTTPS.
- SQLite and uploaded images should be backed up. Uploads are intentionally publicly readable for the fictional profile; don't upload secrets.
- To reset the whole demo, stop Flask, delete `instance/challenge.db`, then run init-db and create-admin again. This deletes all managed content.

## Troubleshooting: Internal Server Error (500)

The database and starter profile are now created automatically when Flask starts. If upgrading from an older ZIP, keep your existing `instance/challenge.db` and `uploads` folder when replacing the code. Do not delete the database unless you want to lose your saved content.

If you still see an Internal Server Error, start with `flask --app app run --debug` in your terminal and copy the final exception/traceback. If you see `no such table`, check that the database path is writable and your `DATABASE_URL` (if set) is correct.
