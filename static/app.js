/* =========================================================================
   Swedish citizenship test — practice quiz (walking skeleton)

   THE ONE IDEA IN THIS FILE
   -------------------------
   The app is organised in three layers, in this order:

     1. STATE   — a single plain object describing everything that is true
                  right now. The single source of truth.
     2. RENDER  — a pure-ish function: read state, make the screen match it.
                  It never *decides* anything, it only reflects.
     3. EVENTS  — clicks change state, then call render(). Nothing else.

   The rule that makes it work: EVENT HANDLERS NEVER TOUCH THE DOM DIRECTLY.
   They mutate state and re-render. If you ever find yourself writing
   `someElement.textContent = ...` inside a click handler, you are drifting
   back toward "the truth is scattered across the page", which is exactly
   the bug factory this structure avoids.

   This is also, in miniature, how React works. Learning it here by hand is
   why React will later feel obvious rather than magic.
   ========================================================================= */


/* ---------------------------------------------------------------------
   1. STATE
   --------------------------------------------------------------------- */

const state = {
  questions: [],      // filled from data/questions.json at startup
  index: 0,           // which question we are on (0-based)
  score: 0,           // correct answers so far
  selected: null,     // index of the option clicked; null = not answered yet
  screen: 'start',    // 'start' | 'quiz' | 'result'
  currentOrder: [],
};

// TODO (save progress): persist { index, score } to localStorage on every
// answer and read it back on load, so refreshing does not lose the run.
// TODO (categories): add `state.filter` and load a subset of questions.


/* ---------------------------------------------------------------------
   1b. DERIVED STATE

   How long one run is. Four places need this number — the progress text,
   the two "is this the last question" checks, and the score denominator —
   and all four mean the same thing, so all four read it from here rather
   than from state.questions.length directly.

   Today a run is every verified question, so that is all this returns. The
   point of the function is not what it computes but that it has a name: when
   a run becomes a sample of the library instead of all of it, this is the
   only place that changes. See "Deferred: a run is the whole set" in PLAN.md
   for why that change is not just a smaller number.
   --------------------------------------------------------------------- */

function runLength() {
  return state.questions.length;
}


/* ---------------------------------------------------------------------
   2. ELEMENT REFERENCES

   Looked up once, at startup, instead of on every render. Cheaper, and it
   fails loudly here rather than mysteriously later.
   --------------------------------------------------------------------- */

const el = {
  screenStart:  document.getElementById('screen-start'),
  screenQuiz:   document.getElementById('screen-quiz'),
  screenResult: document.getElementById('screen-result'),

  btnStart:     document.getElementById('btn-start'),
  btnNext:      document.getElementById('btn-next'),
  btnRestart:   document.getElementById('btn-restart'),

  loadError:    document.getElementById('load-error'),
  questionCount: document.getElementById('question-count'),
  progress:     document.getElementById('progress'),
  questionText: document.getElementById('question-text'),
  options:      document.getElementById('options'),
  feedback:     document.getElementById('feedback'),
  score:        document.getElementById('score'),
  scoreComment: document.getElementById('score-comment'),
};


/* ---------------------------------------------------------------------
   3. LOADING THE DATA

   `fetch` returns a Promise, so this function is `async`. Note that fetch
   only rejects on *network* failure — a 404 still "succeeds" with ok=false,
   which is why the explicit res.ok check below is required, not optional.

   The URL is a path, not a full address: '/api/questions' means "same server
   this page came from". That works locally and in production without change,
   because the API and the frontend are deliberately served from one origin.
   --------------------------------------------------------------------- */

async function loadQuestions() {
  try {
    const res = await fetch('/api/questions');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.questions = data.questions;

    // state.questions.length, not runLength(): this asks "did the library
    // load at all", which is a different question from "how long is a run".
    if (!state.questions || state.questions.length === 0) {
      throw new Error('Inga frågor i filen');
    }
  } catch (err) {
    // Fail visibly. A silent blank screen is the worst possible failure mode.
    el.loadError.textContent =
      `Kunde inte ladda frågorna (${err.message}). Kör du via en lokal server?`;
    el.loadError.hidden = false;
    el.btnStart.disabled = true;
  }
}

// Note: moving from a static file to a real API changed exactly one line —
// the URL — because everything else reads from `state.questions`. That was
// the payoff for keeping content out of code.
//
// TODO (phase 2): the response shape is unchanged ({version, questions}), so
// filtering by category becomes a query string: `/api/questions?category=...`.


/* ---------------------------------------------------------------------
   4. RENDER

   One entry point. Show the screen the state says, then let that screen
   draw itself. Every visual change in the app flows through here.
   --------------------------------------------------------------------- */

function render() {
  el.screenStart.hidden  = state.screen !== 'start';
  el.screenQuiz.hidden   = state.screen !== 'quiz';
  el.screenResult.hidden = state.screen !== 'result';

  if (state.screen === 'start')  renderStart();
  if (state.screen === 'quiz')   renderQuestion();
  if (state.screen === 'result') renderResult();
}

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

function shuffleQuestionOrder() {
    state.currentOrder = [...state.questions[state.index].options.keys()];
    shuffleArray(state.currentOrder);
};

function renderStart() {
  const n = runLength();

  // "1 fråga", not "1 frågor". Reachable today rather than hypothetical:
  // verify exactly one question and the app boots perfectly happily.
  el.questionCount.textContent = n === 1 ? '1 fråga' : `${n} frågor`;

  // Nothing loaded means nothing to promise. loadQuestions() has already
  // shown the error and disabled the button in that case, so the count just
  // stays out of the way.
  el.questionCount.hidden = n === 0;
}


function renderQuestion() {
  const q = state.questions[state.index];
  const answered = state.selected !== null;
  el.progress.textContent = `Fråga ${state.index + 1} av ${runLength()}`;

  // textContent, never innerHTML: textContent treats the string as plain text,
  // so question content can never inject markup or scripts. Habit worth having
  // now, before any of this data comes from somewhere you do not control.
  el.questionText.textContent = q.question;

  // Rebuild the option buttons from scratch each render. Slightly wasteful,
  // completely predictable — the right trade at this size. (Avoiding this
  // waste at scale is essentially what React's virtual DOM is for.)
  el.options.replaceChildren();

  state.currentOrder.forEach(originalIndex => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn option';
    btn.textContent = q.options[originalIndex];

    if (answered) {
      // Once answered, freeze the choices and reveal the truth.
      btn.disabled = true;
      if (originalIndex === q.correctIndex) {
        btn.classList.add('correct');
        btn.textContent = `✓ ${q.options[originalIndex]}`;   // a symbol, not just colour (a11y)
      } else if (originalIndex === state.selected) {
        btn.classList.add('wrong');
        btn.textContent = `✗ ${q.options[originalIndex]}`;
      }
    } else {
      btn.addEventListener('click', () => selectAnswer(originalIndex));
    }

    el.options.appendChild(btn);
  });

  // Feedback + Next button only exist after an answer.
  if (!answered) {
    el.feedback.hidden = true;
    el.btnNext.hidden = true;
    return;
  }

  const isCorrect = state.selected === q.correctIndex;
  const isLast = state.index === runLength() - 1;

  el.feedback.className = `feedback ${isCorrect ? 'is-correct' : 'is-wrong'}`;
  el.feedback.textContent = `${isCorrect ? 'Rätt!' : 'Fel.'} ${q.explanation}`;
  el.feedback.hidden = false;

  el.btnNext.textContent = isLast ? 'Se resultat' : 'Nästa fråga';
  el.btnNext.hidden = false;
}


function renderResult() {
  const total = runLength();
  el.score.textContent = `${state.score} av ${total} rätt`;

  // TODO (scoring rules): the real medborgarskapsprov has a defined pass
  // threshold. Replace this placeholder cutoff, and consider per-category
  // requirements, once the rules are confirmed.
  const passed = state.score / total >= 0.75;
  el.scoreComment.textContent = passed
    ? 'Snyggt jobbat — det där hade räckt.'
    : 'Bra början. Kör en runda till.';
}


/* ---------------------------------------------------------------------
   5. EVENTS — the only place state is allowed to change.
   --------------------------------------------------------------------- */

function startQuiz() {
  state.index = 0;
  state.score = 0;
  state.selected = null;
  state.screen = 'quiz';
  shuffleQuestionOrder()
  render();
}

function selectAnswer(i) {
  if (state.selected !== null) return;   // guard against double-clicks

  state.selected = i;
  if (i === state.questions[state.index].correctIndex) state.score++;

  // TODO (review wrong answers): push {id, selected} onto a state.answers[]
  // array here — that log is what a "repetera fel svar" feature needs.

  render();
}

function nextQuestion() {
  if (state.index === runLength() - 1) {
    state.screen = 'result';
  } else {
    state.index++;
    state.selected = null;   // reset for the new question
    shuffleQuestionOrder()
  }
  render();
}

el.btnStart.addEventListener('click', startQuiz);
el.btnNext.addEventListener('click', nextQuestion);
el.btnRestart.addEventListener('click', startQuiz);


/* ---------------------------------------------------------------------
   6. STARTUP
   --------------------------------------------------------------------- */

loadQuestions().then(render);
