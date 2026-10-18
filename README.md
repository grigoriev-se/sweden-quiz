# Medborgarskapsprovet — practice app (POC)

A practice quiz for the Swedish citizenship test (medborgarskapsprovet).
FastAPI backend, plain HTML/CSS/JavaScript frontend, questions in a JSON file
in this repo. No build step, no database, no frontend framework.

Every served question cites the section and page of UHR's official study
material it was written from, and is only served once a human has checked it
against that page.

**Live: <https://sweden-quiz.onrender.com>** — hosted on Render's free plan, so
it sleeps after 15 minutes of inactivity; the first visit takes about a minute
to wake it.

See [PLAN.md](PLAN.md) for the architecture and roadmap.

## Setup (once)

Needs Python 3.14 (the version is pinned in `.python-version`). On Windows the
`py` launcher picks it explicitly, even with older Pythons installed:

```bash
py -3.14 -m venv .venv
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

Three files, covering different layers:

| File | What it defends |
|---|---|
| `tests/test_models.py` | The rules themselves — what a valid question is. Loads no data, so it still runs when the content is broken. |
| `tests/test_serving.py` | The gate between validated and visible: only verified questions are served. |
| `tests/test_api.py` | The endpoints, and the content in `data/questions.json`. |

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
| `tests/` | Three test files — see **Test it** above. |
| `render.yaml` | Deploy configuration, kept in git rather than in a dashboard. |
| `.github/workflows/tests.yml` | Runs the tests on every pull request. |
| `PLAN.md` | Architecture, phases, decisions and their reasoning. |

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
  "explanation": "Varför svaret är rätt.",
  "source": {"section": "Rubriken i innehållsförteckningen", "page": 1},
  "verified": false
}
```

`correctIndex` is **0-based**: `0` = the first option.

`verified` and `source` are what decide whether the question ever reaches a
user. **A question with `verified: false` is validated and loaded but never
served** — it lives in the repo, visible in pull requests, invisible in the
quiz. That is the intended workflow: draft it unverified, then check the
question, the correct answer *and the explanation* against the cited page
before flipping the flag. A question cannot be `verified: true` without a
`source`; the app refuses to boot.

Both fields are shown above because leaving them out is the one mistake the
app cannot warn you about — `verified` simply defaults to false and the
question goes quietly missing from the quiz. Misspelling a key *is* caught:
unknown fields are rejected at startup.

Option order in the file does not matter: the frontend shuffles the options
of every question on every run, so put the correct answer wherever is
convenient. Nothing in the code assumes four options or any particular number
of questions — both come from the data.

Run `pytest` to check content without starting the server.

## How changes land

`main` is protected: no direct pushes, and no merge until the tests pass.

```bash
git checkout -b short-description
```

Commit, then push and open a pull request:

```bash
git push -u origin short-description
```

GitHub runs the test suite on the PR. Once it is green, squash and merge.
Render deploys `main` automatically, so a merged pull request is live within a
few minutes — and content that fails validation fails the deploy instead of
reaching users.

## Not here yet

No accounts, no database, and no saved progress between visits — refreshing
starts a new run. Questions are categorised by chapter but there is no way to
filter by category yet, and there are only a small number of them.

Planned work is in [PLAN.md](PLAN.md); the code marks where each piece slots
in:

```bash
git grep -n "TODO"
```
