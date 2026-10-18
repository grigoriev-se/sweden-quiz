# Ideas

Unfiltered. Most of these will not happen, and that is the point — writing one
down costs nothing and deleting it costs nothing.

An idea **graduates into PLAN.md** when it becomes a decision or scheduled
work. Until then it lives here, and PLAN.md stays a record of what was decided
rather than everything that was ever considered.

---

## Language toggle (English / Swedish)

A switch so questions can be read in English as well as Swedish.

Unresolved: the exam itself is in Swedish, and most people taking it are also
learning the language. Reading practice questions in English might help
comprehension or might remove the very difficulty worth practising.

Consequence if it happens: every question needs a translated `question`,
`options` and `explanation` — roughly doubling the content work. It also
complicates `verified`, because a translation is not what the book says. The
citation would attest the Swedish original, not the English rendering.

## User-submitted questions, reviewed before publishing

A UI where someone writes a question and submits it — Anki-shaped, in the
sense of people building their own decks.

Unresolved: who reviews it? `verified` currently means *a human checked this
against UHR's book*. User-submitted content has no such source, so either the
flag's meaning changes or submissions need a separate status.

Consequence if it happens: it is the first feature that needs users to **write**
to the server — accounts or at least submissions, moderation, spam. That is
phases 3 and 4 arriving together.

A much smaller version exists: a personal deck kept in `localStorage`, never
sent anywhere. No accounts, no moderation, no backend. Worth considering first.
