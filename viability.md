# Viability — 3 hours

**Finding: the local test fits Dana's cost ceiling and Cole Street's test-only approval. It is not approved for live client records, the Steady Money agreement says nothing about data, and nobody is named to fix the tool after this week.**

## Cost

Dana's ceiling is **$150 a month in running costs across all agencies**. Steady Money is a three-person nonprofit supplier. She will not charge agencies extra and she will not hire a developer. She said Tess could look after it for about an hour a month if it needs no code.

The prototype costs **$0 a month** in hosting, subscriptions, and model fees. It runs on one computer. It does not call, text, or email anyone. It does not send files anywhere. Python and a browser are the requirements. That is not a claim that staff time is free.

Maya's time limit is about **ten minutes per counsellor a week**. She and Joan would be the people who run it. The office volunteer typed the sample once, on a Tuesday morning, and cannot do it every week. If the Friday run stays inside those ten minutes, it fits the limit she set. That has not been timed on a live Friday with Joan.

Twelve agencies renew in January 2027 at $4,800 each. Five require proof. A tool that needs a developer at each agency fails Dana's rule even if the software invoice is zero.

## What this test was allowed to do

Cole Street's director signed a one-page note so this sample could be used for this test only, including going through an AI tool as long as it is not kept or used for training. Maya said the approval was arranged through her. The materials do not say that every agency uses that same one-page path, or that it always takes about two weeks.

Beyond this test, Cole Street's intake form only tells clients that totals with no names may go to funders. Maya said anything more would need a fresh look. The files include names and phone numbers because she sent them as they are kept. They are practice files. They are not a licence to move client records to an outside service.

## Data handling in this build

- The run stays on the agency machine. The site binds to 127.0.0.1.
- Two files are written: the named call list and the anonymous page. Run Checks is on screen only.
- The anonymous page has counts and the definition. It has no client names.
- The tool does not keep a store of clients between runs. A new upload is a new run.
- Nothing in this build trains a model on the agency's files.

The Steady Money agreement "says nothing about data, storage or AI, because we've never handled client records." The files do not settle which privacy law applies when an agency hands client records to an outside service. This note does not state a legal rule. A director would still need a one-page account of what is read, what leaves the agency, where it goes, how long it is kept, and whether it trains anything. Qualified privacy guidance is required before anything goes beyond this test.

## Who fixes it

Tess is the person Dana named for about an hour a month, and only if it needs no code. She has not accepted that work. Joan and Maya can run the written steps. They are not the people who change the parser.

Until someone accepts it, a wrong rule is fixed by the builder: reproduce it on practice data, change the rule, and rerun the tests. Cole Street's director is the person who signs the page. Dana is the person who would have to accept the definitions before a funder pack. Neither has signed these definitions.

## What has to be true before a second agency

- A fresh approval, not Cole Street's test-only note.
- A named person who can run the steps without code, and a named person who fixes a wrong rule.
- Dana's decision on the words "started" and "improved," after she has seen the scores move.
- A path for session 6 scores after 17 November, so the page can stop saying it is halfway.
- Confirmation that $0 of software still fits inside $150 a month once staff time at twelve agencies is counted honestly. Ten minutes times two counsellors times twelve agencies is the time cost. It was not measured this week.
