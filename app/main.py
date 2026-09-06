"""FastAPI application: serves the quiz API and the frontend from one origin.

Run it locally with:

    .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload

`app.main:app` means "in the module app.main, use the object called app".
--reload restarts the server whenever a .py file changes.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .models import QuestionSet

# Paths are resolved relative to THIS file, never the working directory.
# Otherwise the app only works when started from the project root — and the
# server that runs it in production will not start it from where you think.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "questions.json"
STATIC_DIR = BASE_DIR / "static"


def load_questions() -> QuestionSet:
    """Read and validate the content file.

    encoding="utf-8" is not optional. On Windows, read_text() otherwise uses
    the system codepage and mangles å, ä and ö. Always state the encoding.
    """
    raw = DATA_FILE.read_text(encoding="utf-8")
    return QuestionSet.model_validate_json(raw)


# Loaded ONCE, at import time — i.e. at startup, before the server accepts
# any traffic. Two consequences, both deliberate:
#   * broken content crashes the boot, so a bad deploy never serves users;
#   * every request is served from memory, no disk read, no database.
# The cost is that editing questions.json requires a restart. With --reload
# that is automatic; in production a content change means a redeploy, which
# is exactly the "content as code" workflow we chose in PLAN.md.
QUESTION_SET = load_questions()


app = FastAPI(
    title="Medborgarskapsprovet – övning",
    version="0.1.0",
    # Interactive API docs. Moved under /api/ so it does not collide with the
    # static site mounted at /. Visit http://localhost:8000/api/docs — FastAPI
    # generates it from the type hints, for free.
    docs_url="/api/docs",
    redoc_url=None,
)


@app.get("/api/health")
def health() -> dict:
    """Liveness check.

    Hosting platforms ping an endpoint like this to decide whether a deploy
    succeeded and whether the app is still alive. Cheap to add now, annoying
    to add later while debugging a failing deploy.
    """
    return {"status": "ok", "questions": len(QUESTION_SET.questions)}


@app.get("/api/questions", response_model=QuestionSet)
def get_questions() -> QuestionSet:
    """Every question, as one payload.

    `response_model` makes FastAPI validate what we send as well as what we
    receive, and it is what applies the camelCase aliases on the way out.

    Note this includes `correctIndex`: the browser marks answers itself, so
    anyone opening devtools can see the answers. For a self-study tool that is
    fine — cheating yourself is pointless.
    TODO: if scores ever become meaningful (leaderboards, certificates), stop
    sending the answers and move grading to a POST endpoint on the server.
    """
    return QUESTION_SET


# ---------------------------------------------------------------------------
# The static site.
#
# MOUNT ORDER MATTERS. A mount at "/" catches every path that has not already
# been matched, so it must come AFTER the API routes above. Move this line to
# the top of the file and /api/questions would return a 404 from the static
# handler instead of JSON.
#
# html=True makes "/" serve index.html rather than a directory listing.
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# TODO (phase 3): the write path — POST /api/attempts to log which questions
# get answered wrong. That is when a real database earns its place.
