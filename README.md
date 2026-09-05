# Medborgarskapsprovet — practice app (POC)

A walking skeleton for a Swedish citizenship-test practice quiz.
Plain HTML + CSS + JavaScript. No framework, no build step, no dependencies.

## Run it

From this folder:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000> in a browser. Stop the server with `Ctrl+C`.

**Do not just double-click `index.html`.** Browsers block `fetch()` on `file://`
URLs for security, so the questions would never load. Any static server works —
Python's built-in one just happens to need zero installation.

### Check it on your phone

Both devices on the same Wi-Fi, then:

```bash
python -m http.server 8000 --bind 0.0.0.0
```

Find your machine's local IP (`ipconfig` on Windows, look for IPv4 under your
Wi-Fi adapter) and open `http://<that-ip>:8000` on the phone. Windows Firewall
will likely prompt once — allow it on private networks only.

## Files

| File | What it does |
|---|---|
| `index.html` | Page skeleton. All three screens (start / quiz / result) exist at once; JS shows one. |
| `styles.css` | Mobile-first styling. Colours are CSS variables at the top. |
| `app.js` | All logic, in three layers: **state → render → events**. Start reading here. |
| `data/questions.json` | The questions. Content, deliberately separate from code. |
| `DEVLOG.md` | Build journal — learnings and time spent. |

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

`correctIndex` is **0-based**: `0` = first option. Nothing in the code assumes
four options or eight questions — both are read from the data.

Watch for a trailing comma after the last object; JSON does not allow it and the
whole file will fail to parse. The app will tell you if that happens.

## Deliberately not here yet

No accounts, no backend, no database, no saved progress, no categories, no
timer, no real exam content, no tests, no deployment.

Each of those has a `TODO:` comment in the code marking where it slots in.
Find them all with:

```bash
git grep -n "TODO"
```

## Where this goes next

The durable assets are the data shape and the game logic — the rendering layer
is the cheap, replaceable part.

- **Save progress** → `localStorage`, ~10 lines, no new tools.
- **Installable on a phone** → add a PWA manifest + service worker.
- **Real content from a server** → change one `fetch()` URL in `app.js`.
- **Bigger UI** → port to React/Vite when hand-rolled rendering starts to hurt.
- **Deploy** → it is already a static site; GitHub Pages or Netlify take the
  folder as-is, no build.
