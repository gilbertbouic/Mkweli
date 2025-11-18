MkweliAML - Simple AML/KYC Tool
MkweliAML helps check clients against sanctions lists. It runs on your computer. No internet needed after setup. Data stays local. This keeps it private and safe. It is free and open-source. Made for small groups like NGOs. Works on Ubuntu/Linux, Windows, and Mac.

What It Does

* Set up a password to protect access.

* Load sanctions lists from free sources.

* Add client details.

* Check if clients match lists.

* Make reports with proof.

* See stats on dashboard.

* Log actions for records.

Get Started
Follow these steps. They work on Ubuntu/Linux, Windows, or Mac.

1. Install Python if needed. Get Python 3 from python.org. It is free.

2. Download the files. Go to github.com/gilbertbouic/Mkweli. Click Code then Download ZIP.

3. Open the folder. Unzip to a new place on your computer.

4. Set up environment. Open terminal or command prompt. Go to the folder.

   * On Ubuntu/Linux or Mac: Type python3 -m venv venv. Then source venv/bin/activate.

   * On Windows: Type python -m venv venv. Then venv\Scripts\activate.

5. Install needed parts. Type pip install -r requirements.txt.

6. Make database. Type python init_db.py.

7. Start the app. Type python app.py. Open browser to http://localhost:5000.

First Use

* Set a strong password. Use at least 8 letters.

* Lists load on their own if online.

* Add a client to test.

How to Use

* Dashboard shows totals.

* Clients: Add name and details. Click check sanctions.

* Lists: Click refresh if needed. Upload files by hand if offline.

* Reports: Pick client and make PDF.

* Settings: Change your group name.

* Help: Read for more tips.

Fix Problems

* See logs/app.log for errors.

* Test parsers: Type python -m unittest tests/test_parsers.py.

* No internet: Use manual upload.

Update Lists
App loads lists from free places like UN and US sites. It checks for changes.
Safe and Simple
No keys to add. Data is local. Clean duplicates to keep small.
License: Apache-2.0.
Made by Gilbert Clement Bouic. Help from Grok AI.
