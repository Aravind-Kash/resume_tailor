# Deploying Resume Personalizer to Streamlit Cloud

Free hosting, accessible from any computer, takes ~5 minutes.

---

## Step 1 — Get a free Gemini API key

1. Go to [ai.google.dev](https://ai.google.dev) and sign in with Google.
2. Click **Get API key → Create API key**.
3. Copy the key (starts with `AIza...`). Keep it safe.

---

## Step 2 — Push to GitHub

The app must be in a GitHub repo for Streamlit Cloud to deploy it.

```bash
cd Resume_personalizer

# Initialise a git repo (skip if already done)
git init
git add .
git commit -m "Initial commit"

# Create a new repo on github.com (do this in the browser), then:
git remote add origin https://github.com/YOUR_USERNAME/resume-personalizer.git
git branch -M main
git push -u origin main
```

> **Important:** add a `.gitignore` so your API key and generated files
> are never committed:
>
> ```
> .venv/
> jobs/
> __pycache__/
> .streamlit/secrets.toml
> *.pdf
> *.aux
> *.log
> ```

---

## Step 3 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repo, branch `main`, and set **Main file path** to `app.py`.
4. Click **Advanced settings → Secrets** and add:

```toml
GEMINI_API_KEY = "AIza..."
```

5. Click **Deploy**. Streamlit Cloud installs everything from `requirements.txt`
   and `packages.txt` (including TeX Live for PDF compilation).

Your app will be live at:
`https://YOUR_USERNAME-resume-personalizer-app-XXXXX.streamlit.app`

Share that URL between your computers — no install needed on the other machine.

---

## Running locally (no deployment)

```bash
cd Resume_personalizer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Enter your Gemini API key in the key field when the app opens.
If you want to skip that every time, create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "AIza..."
```

---

## How to use

1. Open the app URL from any computer or browser.
2. Upload your `.tex` resume (cached for the session — no re-upload needed per tab).
3. Open a LinkedIn job → scroll to description → select all → copy → paste into the textarea.
4. Click **✨ Tailor My Resume**.
5. Download the PDF (and optionally the `.tex` or `CHANGES.md`).

That's it. One page, one click.
