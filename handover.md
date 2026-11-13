# Handover: Steady Money halfway reporter

This is the written plan for after the builder steps away. It covers who looks after the tool, what it costs to run, what happens when it gets one row wrong, and what it cannot fix.

The Friday run uses three files from a new agency: an attendance sheet, a diary sheet, and counsellor notes. The file names, column headings, and note layout can differ from Cole Street and Bayfield. The tool does not call, text, or email anyone. It does not connect to a funder system. The first run counts. Nobody edits the files or the output by hand.

## Who looks after it

Maya Osei and Joan are the operators at Cole Street. Maya's limit is about ten minutes per counsellor a week. The list has to print on paper. Clients do not log in.

Their steps on a Friday:

1. Save the three files the agency already keeps: attendance, diaries, and counsellor notes. Do not rename columns to match a sample.
2. On the agency computer, start the tool and open http://127.0.0.1:5000.
3. Upload the three files and run them once.
4. Read the agency name and the client count first. If the page says `ERROR: Cannot read notes. Halting.`, stop. Do not invent a results file. Fix the notes file only if it is the agency's own unreadable export, then run once more and treat that new run as the run that counts for that file. On Friday's scored run, the first run is the one that counts.
5. Read Run Checks before the call list. Those lines are names the tool could not attach safely. Do not guess them onto a client.
6. Print the client list. Use it for the Friday calls. A row marked do not contact is not called, texted, or mailed.
7. Give the director the one-page summary only. It has counts and the definition. It has no client names.

Dana approves cost and, later, the definitions of started and improved before a funder pack. The director signs the page. Tess was named for about an hour a month if the tool needs no code. She has not accepted that work.

Nobody is named yet to repair the parser if a rule is wrong. Maya and Joan can follow written steps. They do not change code. Until a maintainer accepts the role, the builder is the person who fixes a wrong rule and reruns the tests.

## What it costs to run

The prototype costs $0 a month in hosting and model fees. It runs on one computer.

Dana's ceiling is $150 a month across all agencies. She will not hire a developer and she will not charge agencies extra. Twelve agencies renew in January 2027. Five of them require proof of progress.

Maya's time is the real running cost she set: about ten minutes per counsellor per week, for her and for Joan. That has not been timed on a live Friday.

## What happens when it gets one wrong

The tool never contacts a client. A wrong row sits on the page until a counsellor reads it.

Three kinds of wrong row:

- **Unclear name.** The note stays in Run Checks. Two people who share a first name, or a last name, are not merged and are not both marked do not contact. Each person keeps the contact on their own attendance row unless a later note matches that one person.
- **Do not contact.** A matched ban is `do not contact`. The row is not a suggestion to call, text, or send paper. Maya said she would stop using the tool the day it told her to contact someone who had asked not to be contacted. One such suggestion fails Friday's whole run, even if the other clients are right.
- **Wrong status.** On track means the client does not have two unexcused absences and does not have two unexcused missed diaries. A diary that was not set, was on hold, was missed because the session ran long, or was "not typed yet" does not count against the client. A household note does not excuse a miss. The "why" column is there so the person covering the desk can see the reason without Maya's memory.

A blank Money Check is missing, not zero. Improved means both scores are present and the second is higher than the first.

If a rule is wrong, stop using that row for a real call. Record the client id and the file names, without copying phone numbers into a chat or a public place. Fix the rule on practice data, then rerun the tests. Do not hand-edit Friday's output to make the score.

## What it cannot fix

- Session 6. It is 17 November 2026 and it is not in this week's files. The page says this is a halfway view. Final scores are not available.
- A signed definition of started, stayed, and improved. The words on the page are proposed so a director can see the movement. Dana has not approved them for a funder.
- Whether Maya and Joan score the five questions the same way. Tess was going to follow up on the score wording. That note is not in these files.
- A diary page Dana has never seen. The diary stays in the client's paper folder. The tool uses diaries only to avoid counting an excused miss as stalled. It does not claim that reminders cause higher Money Check scores.
- A promise or a contact change that was never written down.
- Two people with the same full name and no case number. The tool does not pick one.
- Cole Street's test-only approval. The director's one-page note covers this sample. It does not cover a second agency, and it does not allow the files to be kept or used for training.
- The Steady Money agreement. It says nothing about data, storage, or AI. This handover does not state a privacy-law conclusion. A director needs a separate one-page data note, and qualified privacy guidance, before live use.
- A named maintainer. Tess has not agreed to the hour a month.

## How to run it

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Upload the attendance CSV, the diaries CSV, and the notes file. Leave the terminal open while the page is in use.

The command-line form, for a folder that already holds the three files:

```powershell
python run.py --folder C:\path\to\agency-folder
```

The agency name is taken from the attendance file name. The same name with different rows produces a new result from those rows.
