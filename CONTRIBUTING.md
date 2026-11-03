# Contributing

## Branches
- `main` is always deployable. It publishes to GitHub Pages on every push.
- Work on a branch named `feature/<short-name>` or `fix/<short-name>`.
- Open a pull request into `main`. Do not push directly to `main`.

## Commits
Use short, present-tense messages with a prefix:
- `feat:` new behaviour
- `fix:` bug fix
- `docs:` README or docs only
- `style:` layout or CSS only
- `refactor:` no behaviour change

Example: `fix: keep budget error visible after typing`

## Before you push
1. Open `index.html` in a browser and check the console for errors.
2. Try the budget form (for example budget 50000, discount 500) and a CSV upload.
3. Check the page in light mode, dark mode and on a narrow screen.
4. Run `node --check script.js budget.js config.js` (when Node.js is installed).

## Rules
- No external libraries. Keep charts as plain DOM and SVG.
- Do not claim that a discount caused a purchase. All comparisons are descriptive.
- Keep user data in the browser. Nothing from an uploaded CSV is sent anywhere.
