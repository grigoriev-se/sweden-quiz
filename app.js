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
};

// TODO (save progress): persist { index, score } to localStorage on every
// answer and read it back on load, so refreshing does not lose the run.
// TODO (categories): add `state.filter` and load a subset of questions.


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

   Heads-up: this fetch fails if you open index.html by double-clicking it.
   Browsers block file:// fetches for security. Use the local server — see
   README.md.
   --------------------------------------------------------------------- */

async function loadQuestions() {
  try {
    const res = await fetch('data/questions.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.questions = data.questions;

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

// TODO (real content / backend): swap the URL above for an API endpoint.
// Because everything else reads from `state.questions`, that is the ONLY
// line that changes. This is the payoff for keeping content out of code.


/* ---------------------------------------------------------------------
   4. RENDER

   One entry point. Show the screen the state says, then let that screen
   draw itself. Every visual change in the app flows through here.
   --------------------------------------------------------------------- */

function render() {
  el.screenStart.hidden  = state.screen !== 'start';
  el.screenQuiz.hidden   = state.screen !== 'quiz';
  el.screenResult.hidden = state.screen !== 'result';

  if (state.screen === 'quiz')   renderQuestion();
  if (state.screen === 'result') renderResult();
}


function renderQuestion() {
  const q = state.questions[state.index];
  const answered = state.selected !== null;

  el.progress.textContent = `Fråga ${state.index + 1} av ${state.questions.length}`;

  // textContent, never innerHTML: textContent treats the string as plain text,
  // so question content can never inject markup or scripts. Habit worth having
  // now, before any of this data comes from somewhere you do not control.
  el.questionText.textContent = q.question;

  // Rebuild the option buttons from scratch each render. Slightly wasteful,
  // completely predictable — the right trade at this size. (Avoiding this
  // waste at scale is essentially what React's virtual DOM is for.)
  el.options.replaceChildren();

  q.options.forEach((text, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn option';
    btn.textContent = text;

    if (answered) {
      // Once answered, freeze the choices and reveal the truth.
      btn.disabled = true;
      if (i === q.correctIndex) {
        btn.classList.add('correct');
        btn.textContent = `✓ ${text}`;   // a symbol, not just colour (a11y)
      } else if (i === state.selected) {
        btn.classList.add('wrong');
        btn.textContent = `✗ ${text}`;
      }
    } else {
      btn.addEventListener('click', () => selectAnswer(i));
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
  const isLast = state.index === state.questions.length - 1;

  el.feedback.className = `feedback ${isCorrect ? 'is-correct' : 'is-wrong'}`;
  el.feedback.textContent = `${isCorrect ? 'Rätt!' : 'Fel.'} ${q.explanation}`;
  el.feedback.hidden = false;

  el.btnNext.textContent = isLast ? 'Se resultat' : 'Nästa fråga';
  el.btnNext.hidden = false;
}


function renderResult() {
  const total = state.questions.length;
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
  if (state.index === state.questions.length - 1) {
    state.screen = 'result';
  } else {
    state.index++;
    state.selected = null;   // reset for the new question
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
