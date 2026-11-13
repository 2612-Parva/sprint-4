# How to open and run this

You do not need to know how to code. You need a Windows computer, an internet connection for the first setup, and the three files the agency already keeps: the attendance sheet, the diary sheet, and the counsellor notes.

The tool stays on your computer. It does not call or text anyone, and it does not send the files anywhere else.

## 1. Download the folder

1. Open this link in Chrome or Edge: https://github.com/2612-Parva/sprint-4
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. When the download finishes, open your Downloads folder.
5. Right-click `sprint-4-main.zip` and choose **Extract All**.
6. Click **Extract**. A folder named `sprint-4-main` appears.

Remember where that folder is. You will use it in the next steps.

## 2. Install Python, once

Skip this step if Python is already installed.

1. Open https://www.python.org/downloads/
2. Click the yellow button that says **Download Python**.
3. Open the downloaded installer.
4. On the first screen, tick **Add python.exe to PATH**. This box is at the bottom. If you miss it, the later steps will not work.
5. Click **Install Now**.
6. When it finishes, click **Close**.

## 3. Start the tool

1. Open the `sprint-4-main` folder you extracted.
2. Click the address bar at the top of the folder window, type `powershell`, and press Enter. A blue window opens.
3. Copy this line, paste it into the blue window with a right-click, and press Enter:

```
python -m pip install -r requirements.txt
```

4. Wait until the typing stops and you see a new line you can type on. Then paste this line and press Enter:

```
python app.py
```

5. Wait until the window shows `Running on http://127.0.0.1:5000`.

Leave this blue window open. Closing it turns the tool off.

## 4. Use it in the browser

1. Open Chrome or Edge.
2. Click the address bar and type `http://127.0.0.1:5000`, then press Enter.
3. You should see **Steady Money - Impact Reporter**.
4. Choose the three files in the three boxes:
   - **Attendance (CSV)** is the attendance sheet.
   - **Diaries (CSV)** is the diary sheet.
   - **Notes (TXT)** is the counsellor notes.
5. Click **Process Data** once. Do not edit the files first. The first run is the one that counts.

The first things on the next page are the agency name and the number of clients. Below that you can download two files:

- the one-page summary, with counts and no client names
- the client list, for the Friday calls

Read **Run Checks** before using the client list. Those lines are notes the tool could not attach to one person.

## 5. If something looks wrong

- If the page says `ERROR: Cannot read notes. Halting.`, stop. The tool did not write a results file. Do not type a results file by hand.
- If the blue window says Python was not found, close it, install Python again, and tick **Add python.exe to PATH**.
- If the browser says it cannot connect, look at the blue window. If it is closed, go back to step 3 and run `python app.py` again.
- To stop the tool, click the blue window and press Ctrl+C, or just close that window.

## What you will not find in the download

The practice files from Cole Street and Bayfield are not in this download. They contain client names and phone numbers. Use the three files from the agency you are working with.
