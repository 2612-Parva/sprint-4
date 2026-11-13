# Steady Money Impact Reporter & Triage Tool

This local Python tool finds attendance, diary, and counsellor-note files in an
agency folder. It creates:

- `results.csv`, containing client IDs, triage status, contact method, and reason.
- `summary.md`, containing anonymous agency-level Money Check totals.

The parser discovers files and columns from their contents. It does not depend
on Cole Street, Bayfield, or fixed filenames.

## Command line

Python 3.10 or newer is recommended.

```powershell
python run.py --folder C:\path\to\agency-folder
```

Choose a different output folder:

```powershell
python run.py --folder C:\path\to\agency-folder --output C:\path\to\output
```

If a folder contains more than one agency, select files by filename hint:

```powershell
python run.py --folder . --agency cole-street --output .\output\cole-street
python run.py --folder . --agency bayfield --output .\output\bayfield
```

The command prints the derived agency name and attendance count before
processing notes. If most notes cannot be read, it prints exactly:

```text
ERROR: Cannot read notes. Halting.
```

It does not write either output file on that failed run.

## Web interface

Install the web dependencies and start Flask:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser. Upload the attendance CSV, diaries
CSV, and notes TXT in their separate fields. Click **Process Data**, review the
previews and warnings, and download both generated files.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The automated tests cover the named Bayfield and Cole Street acceptance cases,
anonymous summary output, and the required stop behavior for unreadable notes.

## Privacy

The sample files contain names, phone numbers, and financial information.
Keep the tool and its inputs local. Do not publish sample files or generated
client-level results.
