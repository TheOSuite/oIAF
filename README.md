---

# oIAF: Easy Web Authentication Tester

![GitHub License](https://img.shields.io/github/license/TheOSuite/oXSS)
![Python Version](https://img.shields.io/badge/python-3.13-blue)

Welcome to **oIAF**! This is a simple tool with a graphical interface (GUI) that helps you test web application login forms for common security issues. Think of it as a helpful assistant for checking if a website's login is vulnerable to basic attacks like trying common passwords or figuring out valid usernames.

**Please Note:** This tool is designed for learning and testing on websites you **own or have explicit permission** to test. Using it on other websites without permission is illegal and unethical. Always be responsible!

## What Can oIAF Do?

Here are the main things oIAF can help you check:

*   **Easy to Use:** It has a window you can click and type into, so you don't need to remember complicated commands.
*   **Test Login Pages:** Point it at a website's login page.
*   **Use Your Own Lists:** Provide files with lists of common usernames and passwords to try.
*   **Stay Hidden (Kind of):** Use proxies to make requests seem like they are coming from different places. It can even check if your proxies are working.
*   **Be Gentle:** It can automatically slow down requests if the website seems to be blocking you (rate limiting).
*   **Spot Lockouts:** It tries to figure out if the website locks accounts after too many wrong tries.
*   **Avoid Locked Accounts:** If it thinks an account is locked, it can wait a bit before trying again.
*   **See What's Happening:** Watch the progress and see messages about what the tool is doing in real-time.
*   **Stop Anytime:** You can stop the test whenever you need to.
*   **Summary Report:** Get a list of any accounts that seemed to get locked during the test.

## Getting Started (Prerequisites)

You need a few things on your computer before you can run eIAF:

1.  **Python:** oIAF is written in Python. You need **Python version 3.6 or newer**. You can download it from [python.org](https://www.python.org/). Python usually comes with the parts needed for the GUI (Tkinter).
2.  **Extra Python Libraries:** You need two extra libraries: `requests` (to send web requests) and `beautifulsoup4` (to read website content).

    Open your computer's terminal or command prompt and type this command, then press Enter:

    ```bash
    pip install requests beautifulsoup4
    ```

    This will download and install the libraries.

## How to Get oIAF

1.  You can get the script by visiting the GitHub repository: [(https://github.com/TheOSuite/oIAF.git)]
2.  Click the green "Code" button and choose "Download ZIP".
3.  Extract the downloaded ZIP file to a folder on your computer.
4.  Inside the folder, you'll find the script file named `oIAF.py`.

## How to Use oIAF

1.  Open your computer's terminal or command prompt.
2.  Use the `cd` command to go to the folder where you saved `oIAF.py`. For example, if it's in your "Downloads" folder:
    ```bash
    cd Downloads
    ```
3.  Once you are in the correct folder, run the script:
    ```bash
    python oIAF.py
    ```
4.  A window titled "Auth Test Module" will pop up.

### Inside the oIAF Window:

*   **Target Login URL:** Type the web address of the login page you want to test (like `https://example.com/login`).
*   **Username Field:** This needs the technical name of the box where you type the username on the website. You can usually find this by right-clicking the username box on the website, selecting "Inspect" or "Inspect Element", and looking for the `name="..."` part inside the `<input>` tag. It might be `username`, `user`, `login`, etc.
*   **Password Field:** Do the same as above, but for the password box. Look for `name="..."` inside the password input tag (`<input type="password"...>`). It might be `password`, `pass`, `pwd`, etc.
*   **Select Usernames File:** Click this button to pick a text file (`.txt`) from your computer that has a list of usernames you want to try, one username per line.
*   **Select Passwords File:** Click this button to pick a text file (`.txt`) with a list of passwords, one password per line.
    *   *If you don't select files, the tool will use a small built-in list of common usernames and passwords.*
*   **Proxies (comma-separated):** If you have a list of proxies (like `192.168.1.1:8080`), type them here separated by commas. Proxies can help if the website blocks your IP address.
*   **Check Proxies:** Click this after entering proxies to see which ones are working.
*   **Initial Delay (s):** This is how long (in seconds) the tool waits between each attempt at first.
*   **Delay Multiplier:** If the website starts blocking or rate limiting, this number tells the tool how much to increase the waiting time.
*   **Max Delay (s):** The longest the tool will wait between attempts, even if it's being blocked.
*   **Lockout Resume Delay (s):** If the tool thinks an account is locked, it will wait this many seconds before trying that username again.
*   **Lockout Text Indicators (comma-separated):** These are words or phrases (like "account locked" or "too many tries") that, if they appear on the login page after a failed attempt, might mean the account is locked. Enter them separated by commas. The tool doesn't care about capitalization here.
*   **Lockout Status Codes (comma-separated):** These are special numbers (like 423, 401, 403) that a web server sends back. Some numbers can also mean an account is locked. Enter them separated by commas.
*   **Run Authentication Scan:** Click this button to start testing!
*   **Stop Scan:** Click this if you want to stop the test early.
*   **Progress:** This bar shows you how far along the test is.
*   **Output Log:** This box shows you messages about what's happening during the test.

### Running Your First Scan

1.  Fill in the **Target Login URL**, **Username Field**, and **Password Field**.
2.  Choose your username and password files if you have them.
3.  Adjust the delay and lockout settings if you know what you're doing, or leave the default values.
4.  Click **Run Authentication Scan**.
5.  Watch the **Output Log** to see messages. Look for `[!!!]` messages - these are important findings like a weak password or a potential account lockout.
6.  When the test finishes (or you click Stop), the **Output Log** will show a summary, including any accounts that might be locked.

## Understanding the Messages

The messages in the **Output Log** help you understand what's happening:

*   `[✓]` : Everything is good!
*   `[i]` : Just some information for you.
*   `[!]` : Something interesting was found (like a username that seems to exist).
*   `[⚠️]` : Be careful! The website might be trying to block or limit you. The tool might increase the delay.
*   `[!!!]` : Important discovery! This could be a weak password found or a potential account lockout.
*   `[X]` : An error happened (like a website connection problem).

If you see `[!!!] Possible Account Lockout Detected...`, it means the tool thinks that specific username might be temporarily or permanently locked because of too many failed attempts. It will usually stop trying passwords for that username for a while.

## Remember: Be Responsible!

This tool is powerful, but it's your responsibility to use it legally and ethically. Only test websites where you have permission.

---
