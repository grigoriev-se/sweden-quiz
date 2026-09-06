# Medborgarskapsprovet — practice app (POC)

A walking skeleton for a Swedish citizenship-test practice quiz.
FastAPI backend, plain HTML/CSS/JavaScript frontend, questions in a JSON file.
No build step, no database, no framework on the frontend.

See [PLAN.md](PLAN.md) for the architecture and roadmap.

## Setup (once)

```bash
python -m venv .venv
```

Then install dependencies:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

## Run it

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open <http://localhost:8000>. `Ctrl+C` stops it.

`app.main:app` means "the object named `app`, in the module `app/main.py`".
`--reload` restarts the server whenever a `.py` file changes — handy in
development, never used in production.

Editing `data/questions.json` also requires a restart, because the content is
loaded and validated once at startup. `--reload` does not watch data files, so
restart by hand after changing questions.

Other useful URLs:

| URL | What |
|---|---|
| <http://localhost:8000/api/questions> | The raw JSON the frontend fetches |
| <http://localhost:8000/api/health> | Liveness check used by the host |
| <http://localhost:8000/api/docs> | Interactive API docs, generated from the type hints |

## Test it

```bash
.venv\Scripts\python.exe -m pytest -v
```

Covers both the API and the *content* — every question is checked for an
in-range answer, non-empty text and no duplicate options.

## Check it on your phone

Both devices on the same Wi-Fi. Uvicorn only listens on localhost by default,
so bind it to every interface:

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0
```

Find this machine's local IP (`ipconfig`, IPv4 under the Wi-Fi adapter; starts
with `192.168.`) and open `http://<that-ip>:8000` on the phone.

Windows Firewall prompts on the first external connection: allow it on
**private** networks only. If the page never loads, suspect the firewall first.

## Layout

| Path | What it does |
|---|---|
| `app/main.py` | FastAPI app: the API routes, and serving the static files. |
| `app/models.py` | Pydantic models. The contract for what a valid question is. |
| `data/questions.json` | The questions. Content, deliberately separate from code. |
| `static/index.html` | Page skeleton. Three screens exist at once; JS shows one. |
| `static/styles.css` | Mobile-first styling. Colours are CSS variables at the top. |
| `static/app.js` | Frontend logic: **state → render → events**. Start reading here. |
| `tests/test_api.py` | API and content tests. |
| `PLAN.md` | Architecture, phases, open questions. |
| `DEVLOG.md` | Build journal. |

Only `static/` is exposed to the web. Everything else — including `.git/` — stays
private. That is the whole reason the frontend lives in its own folder.

## Adding questions

Append an object to the `questions` array in `data/questions.json`:

```json
{
  "id": "q9",
  "category": "historia",
  "question": "Frågetext?",
  "options": ["Alternativ A", "Alternativ B", "Alternativ C", "Alternativ D"],
  "correctIndex": 0,
  "explanation": "Varför svaret är rätt."
}
```

`correctIndex` is **0-based**: `0` = the first option. Nothing in the code
assumes four options or eight questions — both come from the data.

The app validates all of this at startup and **refuses to boot** if anything is
wrong: an out-of-range `correctIndex`, a duplicate `id`, a missing field, a
trailing comma. The error names the offending question. Run `pytest` to check
content without starting the server.

## Not here yet

No accounts, no database, no saved progress, no categories, no real exam
content, no deployment. Each has a `TODO:` comment marking where it slots in:

```bash
git grep -n "TODO"
```
