# Feasibility — 7 hours

**Finding: a local tool can read two agencies that do not share file names, column headings, or note layout, and it can stop when the notes cannot be read. Friday's unseen agency is still a first run. The 2,000 tests lower the chance of a known miss. They do not prove the unseen file.**

The brief says the file names, the column headings, and the way dates and names are written will differ from the samples. If the tool cannot read most of the notes, it must stop and say so, and it must not write results. The exact line is `ERROR: Cannot read notes. Halting.` The agency name, taken from the file name, and the client count come first. The first run counts. No hand edits.

## What had to work before any score mattered

Three traps sit in the samples and would mark a real client wrong if they were ignored.

1. **A blank is missing, not zero.** Sofia's session 4 Money Check is blank because she was away with notice. Carol's week 3 diary says "not typed yet." Scoring either as a failure would mark the client wrongly.
2. **The same cell can mean three different things.** The diary file can show a miss when the counsellor did not set the diary, when it was put on hold by agreement, or when the client did not do it. Only the third counts against the client. "On hold" and "away" apply to later weeks. "Household" does not excuse anyone.
3. **The same first name is not the same person.** Cole Street has two Alexes. Notes use Ray, Liz, Tony, Bill, Gord, and Terry for Raymond, Elizabeth, Anthony, William, Gordon, and Terrence. A returning client gets a new row. An unclear name is a warning. It is not copied onto every person who shares that name.

Status is on track unless there are two or more unexcused absences, or two or more unexcused missed diaries. One of each stays on track. The newest contact line wins, including a later line on the same day. Notes beat the day-one column. A partial "no texts" is not a full ban. A full ban, including "no calls, no texts, and no emails," is do not contact.

## What was run

The tool reads an attendance sheet, a diary sheet, and a notes file. It does not depend on the names Cole Street or Bayfield. The same agency name with different rows is read again from those rows.

- Cole Street, compared with Maya's marked-up list: **48 of 48** on status and way to reach. Maya said she marked Joan's 24 from Joan's notes and a talk with her, and she expected to differ on a few borderline people. This comparison is one counsellor's judgment, not a funder key. On this sample there was no disagreement.
- Bayfield, a second layout the tool had not been written around: 6 clients, agency name Bayfield, halfway page, no client names. There is no answer key for Bayfield in the files, so this check is that the files load and the page follows the rules.
- Generated holdouts in the shapes used by earlier Friday files: later dates, initials, credentials such as "PT," accents, a trial row left on the sheet, and an older "do not contact" still sitting in the file. The newest fact wins. The trial row stays in the started count. One odd row does not remove the others.
- The automated suite is **2,000 tests**, all passing. They cover contact wording, date styles, split first and last names, week columns, Money Check columns in either order, unreadable notes, and the rule that a do-not-contact client is not given call, text, or paper.

## Friday's check

A client is right only when both status and way to reach match. The target named in the scoring note is 12 of 15. Any contact suggestion for someone who asked not to be contacted fails the whole run.

The outputs are two files:

- `results.csv`: `client_id`, `status`, `way_to_reach`, `why`
- the one-page agency view: started, both Money Checks, improved, the definition of improved, and the halfway note. No client names.

If most notes cannot be read, neither file is written.
