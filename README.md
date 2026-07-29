# Spendly — Personal Expense Tracker

A web app for logging personal expenses and understanding where your money goes. Users create an account, record each expense with a category, amount, date, and description, then review their spending through category breakdowns, monthly summaries, and date-range filters.

Amounts are denominated in Indian rupees (₹).

> **Project status:** this repository is a teaching scaffold. The landing page, sign-in page, and registration page are fully built and styled; the data layer and most application logic are intentionally left as exercises (see [Roadmap](#roadmap)).

## What works today

| Route | Method | Status |
|---|---|---|
| `/` | GET | Landing page — hero, feature cards, call-to-action |
| `/register` | GET | Registration form, rendered and styled |
| `/login` | GET | Sign-in form, rendered and styled |

Both forms `POST` back to their own URLs, but the routes are currently GET-only, so submitting one returns HTTP 405 until the handlers are implemented.

The remaining routes are stubs that return a placeholder string rather than a page:

`/logout` · `/profile` · `/expenses/add` · `/expenses/<id>/edit` · `/expenses/<id>/delete`

## Tech stack

**Backend**

- **Python 3.13**
- **Flask 3.1.3** — routing, request handling, templating entry point
- **Werkzeug 3.1.6** — WSGI layer; also the intended source of password hashing helpers
- **Jinja2 3.1.6** — server-side templates with a shared `base.html` layout and block inheritance
- **SQLite** — planned persistence via Python's built-in `sqlite3` (no ORM); the database file `expense_tracker.db` is git-ignored

**Frontend**

- **Hand-written CSS** (`static/css/style.css`, ~530 lines) — no framework. Design tokens are declared as CSS custom properties on `:root`: an ink/paper neutral scale, a forest-green primary accent (`#1a472a`), an amber secondary, plus radius and layout scales.
- **Vanilla JavaScript** (`static/js/main.js`) — currently empty; no build step, bundler, or npm dependencies anywhere in the project.
- **Google Fonts** — DM Serif Display for headings, DM Sans for body text.

**Testing**

- **pytest 8.3.5** with **pytest-flask 1.3.0** — installed and pinned; no test suite has been written yet.

## Project structure

```
expense-tracker/
├── app.py                 # Flask app + all route definitions
├── database/
│   ├── __init__.py        # (empty)
│   └── db.py              # stub: get_db(), init_db(), seed_db() to be written
├── templates/
│   ├── base.html          # shared layout — nav, main block, footer
│   ├── landing.html       # marketing page
│   ├── login.html         # sign-in form
│   └── register.html      # registration form
├── static/
│   ├── css/style.css      # full stylesheet
│   └── js/main.js         # (empty)
├── requirements.txt
└── .gitignore
```

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

The development server runs with `debug=True` on **port 5001**:

http://127.0.0.1:5001

## Roadmap

The stub comments in the source track a numbered sequence of exercises:

| Step | Work |
|---|---|
| 1 | Database setup — `get_db()` with `row_factory` and foreign keys enabled, `init_db()` using `CREATE TABLE IF NOT EXISTS`, `seed_db()` for sample data |
| 2 | Registration — accept `POST`, hash passwords, persist users |
| 3 | Sessions — sign in and `/logout` |
| 4 | `/profile` page |
| 5–6 | Expense listing, category breakdowns, monthly summaries, date-range filters |
| 7 | `/expenses/add` |
| 8 | `/expenses/<id>/edit` |
| 9 | `/expenses/<id>/delete` |

Steps 2, 5, and 6 are inferred from the gaps between the numbers referenced in `app.py` and `database/db.py`.
