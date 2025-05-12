import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import os
from bs4 import BeautifulSoup
import random
import queue
import time

class AuthTestModule:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.user_file = None
        self.pass_file = None
        self.proxies = []
        self.is_scanning = False
        self._scan_thread = None
        self.total_attempts = 0
        self.completed_attempts = 0
        self.locked_accounts = {} # Dictionary to store potentially locked accounts and reasons

        # Configuration for dynamic delays - INITIALIZE THESE FIRST
        self.initial_delay = 0.5 # seconds
        self.current_delay = self.initial_delay
        self.delay_multiplier = 2 # Factor to increase delay when rate limited
        self.max_delay = 30 # Maximum delay
        self.lockout_resume_delay = 300 # Delay before attempting to resume testing a locked account (seconds)

        # Account Lockout Detection Configuration (defaults) - INITIALIZE THESE FIRST
        self.lockout_indicators_config = [
            ("account locked", "high"),
            ("too many failed login attempts", "high"),
            ("account temporarily unavailable", "medium"),
            ("please try again later", "low"),
            ("account disabled", "high"),
            ("maximum login attempts exceeded", "high"),
        ]
        self.lockout_status_codes_config = [
            (423, "high"), # 423 Locked is a specific code
            (401, "medium"), # 401 Unauthorized (can sometimes indicate lockout after multiple attempts)
            (403, "medium"), # 403 Forbidden (can sometimes indicate block/lockout)
        ]

        self.create_widgets() # Call create_widgets AFTER variables are initialized

        self.fake_headers = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/109.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'},
        ]

        # Configuration for dynamic delays
        self.initial_delay = 0.5 # seconds
        self.current_delay = self.initial_delay
        self.delay_multiplier = 2 # Factor to increase delay when rate limited
        self.max_delay = 30 # Maximum delay
        self.lockout_resume_delay = 300 # Delay before attempting to resume testing a locked account (seconds)

        # Account Lockout Detection Configuration (defaults)
        self.lockout_indicators_config = [
            ("account locked", "high"),
            ("too many failed login attempts", "high"),
            ("account temporarily unavailable", "medium"),
            ("please try again later", "low"),
            ("account disabled", "high"),
            ("maximum login attempts exceeded", "high"),
        ]
        self.lockout_status_codes_config = [
            (423, "high"), # 423 Locked
            (401, "medium"), # 401 Unauthorized (can sometimes indicate lockout after multiple attempts)
            (403, "medium"), # 403 Forbidden (can sometimes indicate block/lockout)
        ]

    def create_widgets(self):
        ttk.Label(self.frame, text="Target Login URL:").grid(row=0, column=0, sticky='w')
        self.url_entry = ttk.Entry(self.frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.frame, text="Username Field:").grid(row=1, column=0, sticky='w')
        self.user_field = ttk.Entry(self.frame, width=20)
        self.user_field.insert(0, 'username')
        self.user_field.grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(self.frame, text="Password Field:").grid(row=2, column=0, sticky='w')
        self.pass_field = ttk.Entry(self.frame, width=20)
        self.pass_field.insert(0, 'password')
        self.pass_field.grid(row=2, column=1, sticky='w', padx=5)

        ttk.Button(self.frame, text="Select Usernames File", command=self.load_user_file).grid(row=3, column=0, pady=5)
        self.user_file_label = ttk.Label(self.frame, text="No file selected")
        self.user_file_label.grid(row=3, column=1, sticky='w')

        ttk.Button(self.frame, text="Select Passwords File", command=self.load_pass_file).grid(row=4, column=0, pady=5)
        self.pass_file_label = ttk.Label(self.frame, text="No file selected")
        self.pass_file_label.grid(row=4, column=1, sticky='w')

        # Proxy input field
        ttk.Label(self.frame, text="Proxies (comma-separated, e.g., ip:port):").grid(row=5, column=0, sticky='w')
        self.proxy_entry = ttk.Entry(self.frame, width=50)
        self.proxy_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(self.frame, text="Check Proxies", command=self.check_proxies_thread).grid(row=6, column=0, columnspan=2, pady=5)

        # Delay configuration
        ttk.Label(self.frame, text="Initial Delay (s):").grid(row=7, column=0, sticky='w')
        self.initial_delay_entry = ttk.Entry(self.frame, width=10)
        self.initial_delay_entry.insert(0, str(self.initial_delay))
        self.initial_delay_entry.grid(row=7, column=1, sticky='w', padx=5)

        ttk.Label(self.frame, text="Delay Multiplier:").grid(row=8, column=0, sticky='w')
        self.delay_multiplier_entry = ttk.Entry(self.frame, width=10)
        self.delay_multiplier_entry.insert(0, str(self.delay_multiplier))
        self.delay_multiplier_entry.grid(row=8, column=1, sticky='w', padx=5)

        ttk.Label(self.frame, text="Max Delay (s):").grid(row=9, column=0, sticky='w')
        self.max_delay_entry = ttk.Entry(self.frame, width=10)
        self.max_delay_entry.insert(0, str(self.max_delay))
        self.max_delay_entry.grid(row=9, column=1, sticky='w', padx=5)

        ttk.Label(self.frame, text="Lockout Resume Delay (s):").grid(row=10, column=0, sticky='w')
        self.lockout_resume_delay_entry = ttk.Entry(self.frame, width=10)
        self.lockout_resume_delay_entry.insert(0, str(self.lockout_resume_delay))
        self.lockout_resume_delay_entry.grid(row=10, column=1, sticky='w', padx=5)

        # Lockout Indicators Configuration (basic implementation)
        ttk.Label(self.frame, text="Lockout Text Indicators (comma-separated):").grid(row=11, column=0, sticky='w')
        self.lockout_text_indicators_entry = ttk.Entry(self.frame, width=50)
        self.lockout_text_indicators_entry.insert(0, ", ".join([ind for ind, level in self.lockout_indicators_config]))
        self.lockout_text_indicators_entry.grid(row=11, column=1, padx=5, pady=5)

        ttk.Label(self.frame, text="Lockout Status Codes (comma-separated):").grid(row=12, column=0, sticky='w')
        self.lockout_status_codes_entry = ttk.Entry(self.frame, width=50)
        self.lockout_status_codes_entry.insert(0, ", ".join([str(code) for code, level in self.lockout_status_codes_config]))
        self.lockout_status_codes_entry.grid(row=12, column=1, padx=5, pady=5)

        # Run and Stop buttons in the same row, different columns
        self.run_button = ttk.Button(self.frame, text="Run Authentication Scan", command=self.run_scan_thread)
        # Place in row 13, column 0
        self.run_button.grid(row=13, column=0, pady=10, sticky='w') # Use sticky='w' or 'e' to align

        # Stop button
        self.stop_button = ttk.Button(self.frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED)
        # Place in row 13, column 1
        self.stop_button.grid(row=13, column=1, pady=10, sticky='w', padx=5) # Use sticky='w' or 'e' to align

        # Progress bar
        ttk.Label(self.frame, text="Progress:").grid(row=14, column=0, sticky='w')
        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=14, column=1, padx=5, pady=5)

        self.output_text = tk.Text(self.frame, height=8, width=80) # Adjusted height
        self.output_text.grid(row=15, column=0, columnspan=2, padx=5, pady=5)

    def load_user_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.user_file = file_path
            self.user_file_label.config(text=os.path.basename(file_path))

    def load_pass_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.pass_file = file_path
            self.pass_file_label.config(text=os.path.basename(file_path))

    def load_lines_from_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.log_output(f"[X] Error loading file '{path}': {e}")
            return []

    def log_output(self, msg):
        self.parent.after(0, self._insert_log, msg)

    def _insert_log(self, msg):
        self.output_text.insert(tk.END, msg + "\n")
        self.output_text.see(tk.END)

    def update_progress(self, value):
        self.parent.after(0, self.progress_bar.config, {'value': value})

    def check_proxies_thread(self):
        proxy_string = self.proxy_entry.get()
        if not proxy_string:
            self.log_output("[!] No proxies entered to check.")
            return

        self.proxies = []
        self.log_output("=== Checking Proxies ===")
        thread = threading.Thread(target=self.check_proxies, args=(proxy_string,))
        thread.start()

    def check_proxies(self, proxy_string):
        proxy_list_raw = [p.strip() for p in proxy_string.split(',') if p.strip()]
        tested_count = 0
        working_proxies = []
        total_proxies = len(proxy_list_raw)

        for proxy_addr in proxy_list_raw:
            tested_count += 1
            self.log_output(f"[i] Checking proxy {tested_count}/{total_proxies}: {proxy_addr}")
            try:
                formatted_proxy = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"}
                test_url = "http://httpbin.org/ip"
                r = requests.get(test_url, proxies=formatted_proxy, timeout=5)
                if r.status_code == 200:
                    try:
                        ip_info = r.json()
                        origin_ip = ip_info.get('origin', 'N/A')
                        self.log_output(f"[✓] Proxy {proxy_addr} is working (Origin IP: {origin_ip})")
                        working_proxies.append(formatted_proxy)
                    except Exception as json_e:
                         self.log_output(f"[✓] Proxy {proxy_addr} is working (could not parse origin IP: {json_e})")
                         working_proxies.append(formatted_proxy)
                else:
                    self.log_output(f"[X] Proxy {proxy_addr} failed with status code: {r.status_code}")
            except requests.exceptions.Timeout:
                self.log_output(f"[X] Proxy {proxy_addr} timed out.")
            except requests.exceptions.ConnectionError as e:
                self.log_output(f"[X] Proxy {proxy_addr} connection error: {e}")
            except Exception as e:
                self.log_output(f"[X] Unexpected error checking proxy {proxy_addr}: {e}")

        self.proxies = working_proxies
        self.log_output(f"\n=== Proxy Check Complete: {len(self.proxies)} working proxies found ===")
        if not self.proxies:
            self.log_output("[!] No working proxies available. Authentication tests will run without proxies.")

    def get_random_proxy(self):
        if self.proxies:
            return random.choice(self.proxies)
        return None

    def run_scan_thread(self):
        if self.is_scanning:
            self.log_output("[!] Scan is already in progress.")
            return

        # Load delay and lockout configurations from GUI
        try:
            self.initial_delay = float(self.initial_delay_entry.get())
            self.delay_multiplier = float(self.delay_multiplier_entry.get())
            self.max_delay = float(self.max_delay_entry.get())
            self.lockout_resume_delay = float(self.lockout_resume_delay_entry.get())

            if self.initial_delay < 0 or self.delay_multiplier < 1 or self.max_delay < self.initial_delay or self.lockout_resume_delay < 0:
                 self.log_output("[!] Invalid delay configuration. Using defaults.")
                 self._reset_delay_entries()
        except ValueError:
            self.log_output("[!] Invalid delay configuration. Using defaults.")
            self._reset_delay_entries()

        try:
            text_indicators_raw = [ind.strip() for ind in self.lockout_text_indicators_entry.get().split(',') if ind.strip()]
            status_codes_raw = [code.strip() for code in self.lockout_status_codes_entry.get().split(',') if code.strip()]

            # For simplicity, assigning 'high' confidence to user-provided indicators for now
            self.lockout_indicators_config = [(ind, "high") for ind in text_indicators_raw]
            self.lockout_status_codes_config = []
            for code_str in status_codes_raw:
                try:
                    code = int(code_str)
                    self.lockout_status_codes_config.append((code, "high"))
                except ValueError:
                    self.log_output(f"[X] Invalid status code entered: {code_str}. Skipping.")

        except Exception as e:
            self.log_output(f"[X] Error loading lockout indicators configuration: {e}. Using defaults.")
            # Reset to default configurations if parsing fails
            self._reset_lockout_config_entries()


        self.current_delay = self.initial_delay # Reset current delay at the start of the scan
        self.locked_accounts = {} # Clear locked accounts list for a new scan

        self.is_scanning = True
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.config(value=0)

        self._scan_thread = threading.Thread(target=self.run_auth_tests)
        self._scan_thread.start()

    def _reset_delay_entries(self):
        self.initial_delay = 0.5
        self.delay_multiplier = 2
        self.max_delay = 30
        self.lockout_resume_delay = 300
        self.initial_delay_entry.delete(0, tk.END)
        self.initial_delay_entry.insert(0, str(self.initial_delay))
        self.delay_multiplier_entry.delete(0, tk.END)
        self.delay_multiplier_entry.insert(0, str(self.delay_multiplier))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(self.max_delay))
        self.lockout_resume_delay_entry.delete(0, tk.END)
        self.lockout_resume_delay_entry.insert(0, str(self.lockout_resume_delay))

    def _reset_lockout_config_entries(self):
         self.lockout_indicators_config = [
            ("account locked", "high"), ("too many failed login attempts", "high"),
            ("account temporarily unavailable", "medium"), ("please try again later", "low"),
            ("account disabled", "high"), ("maximum login attempts exceeded", "high"),
        ]
         self.lockout_status_codes_config = [(423, "high"), (401, "medium"), (403, "medium")]
         self.lockout_text_indicators_entry.delete(0, tk.END)
         self.lockout_text_indicators_entry.insert(0, ", ".join([ind for ind, level in self.lockout_indicators_config]))
         self.lockout_status_codes_entry.delete(0, tk.END)
         self.lockout_status_codes_entry.insert(0, ", ".join([str(code) for code, level in self.lockout_status_codes_config]))


    def stop_scan(self):
        self.is_scanning = False
        self.log_output("[!] Scan stopping...")

    def run_auth_tests(self):
        url = self.url_entry.get()
        user_field = self.user_field.get()
        pass_field = self.pass_field.get()

        if not url or not user_field or not pass_field:
            self.log_output("[X] Please provide the target URL, username field, and password field.")
            self._finish_scan()
            return

        usernames = self.load_lines_from_file(self.user_file) if self.user_file else ['admin', 'user', 'test']
        passwords = self.load_lines_from_file(self.pass_file) if self.pass_file else ['password', '123456', 'admin', 'letmein']

        self.total_attempts = 2 + len(usernames) + len(passwords)
        self.completed_attempts = 0
        self.locked_accounts = {} # Clear locked accounts for a new scan

        if not self.is_scanning: self._finish_scan(); return
        self.check_captcha_and_bot_protection(url)
        self.completed_attempts += 1
        self.update_progress((self.completed_attempts / self.total_attempts) * 100)

        if not self.is_scanning: self._finish_scan(); return
        self.perform_user_enumeration(url, user_field, pass_field, usernames)

        if not self.is_scanning: self._finish_scan(); return
        self.test_weak_passwords(url, user_field, pass_field, passwords)

        if not self.is_scanning: self._finish_scan(); return
        self.check_session_cookies(url)
        self.completed_attempts += 1
        self.update_progress((self.completed_attempts / self.total_attempts) * 100)

        self.log_output("\n=== Authentication Scan Complete ===")
        self._report_locked_accounts() # Report locked accounts at the end
        self._finish_scan()

    def _finish_scan(self):
         self.is_scanning = False
         self.parent.after(0, self.run_button.config, {'state': tk.NORMAL})
         self.parent.after(0, self.stop_button.config, {'state': tk.DISABLED})
         if self.completed_attempts >= self.total_attempts:
             self.parent.after(0, self.progress_bar.config, {'value': 100})
         else:
             self.parent.after(0, self.progress_bar.config, {'value': 0})

    def _report_locked_accounts(self):
        if self.locked_accounts:
            self.log_output("\n=== Potentially Locked Accounts ===")
            for username, reasons in self.locked_accounts.items():
                self.log_output(f"- {username}: {', '.join(reasons)}")
        else:
            self.log_output("\n=== No Potentially Locked Accounts Detected ===")


    def _apply_delay(self):
        """Applies the current delay."""
        time.sleep(self.current_delay)

    def _increase_delay(self, reason=""):
        """Increases the current delay based on the multiplier, up to the max delay."""
        old_delay = self.current_delay
        self.current_delay = min(self.max_delay, self.current_delay * self.delay_multiplier)
        if self.current_delay > old_delay:
            self.log_output(f"[!] Increasing delay to {self.current_delay:.2f} seconds ({reason})")

    def _check_lockout_indicators(self, response):
        """Checks response body and status code for lockout indicators with confidence levels."""
        detected_indicators = []

        # Check status codes
        for code, level in self.lockout_status_codes_config:
            if response.status_code == code:
                detected_indicators.append(f"Status code {code} ({level} confidence)")

        # Check response text
        response_text_lower = response.text.lower()
        for indicator, level in self.lockout_indicators_config:
            if indicator in response_text_lower:
                detected_indicators.append(f"Response text contains '{indicator}' ({level} confidence)")

        return bool(detected_indicators), detected_indicators

    def check_captcha_and_bot_protection(self, url):
        if not self.is_scanning: return
        self.log_output("=== CAPTCHA / Bot Protection Check ===")
        try:
            headers = random.choice(self.fake_headers)
            proxy = self.get_random_proxy()
            r = requests.get(url, headers=headers, proxies=proxy, timeout=10)

            soup = BeautifulSoup(r.text, 'html.parser')
            iframe_tags = soup.find_all('iframe', src=True)
            suspicious_iframes = [iframe['src'] for iframe in iframe_tags if 'captcha' in iframe['src'].lower()]

            script_tags = soup.find_all('script')
            script_indicators = [s for s in script_tags if 'bot' in str(s).lower() or 'challenge' in str(s).lower()]

            if suspicious_iframes:
                self.log_output(f"[⚠️] CAPTCHA iframe detected: {suspicious_iframes}")
                self._increase_delay(reason="CAPTCHA iframe detected")
            elif script_indicators:
                self.log_output(f"[⚠️] Suspicious JS challenge detected ({len(script_indicators)} scripts)")
                self._increase_delay(reason="Suspicious JS challenge detected")
            else:
                self.log_output("[✓] No obvious CAPTCHA or bot protection detected.")

            # Check for common rate limit status codes
            if r.status_code == 429:
                 self.log_output("[⚠️] Received 429 Too Many Requests. Increasing delay.")
                 self._increase_delay(reason="429 Too Many Requests")
            elif r.status_code == 403:
                 self.log_output("[⚠️] Received 403 Forbidden. May indicate bot protection. Increasing delay.")
                 self._increase_delay(reason="403 Forbidden")

        except requests.exceptions.Timeout:
            self.log_output(f"[X] Request timed out during CAPTCHA check. Increasing delay.")
            self._increase_delay(reason="Request timeout during CAPTCHA check")
        except requests.exceptions.ConnectionError as e:
             self.log_output(f"[X] Connection error during CAPTCHA check: {e}. Increasing delay.")
             self._increase_delay(reason="Connection error during CAPTCHA check")
        except Exception as e:
            self.log_output(f"[X] Unexpected error checking CAPTCHA/JS: {e}")
        finally:
            self._apply_delay()

    def perform_user_enumeration(self, url, user_field, pass_field, usernames):
        if not self.is_scanning: return
        self.log_output("\n=== User Enumeration Test ===")
        for username in usernames:
            if not self.is_scanning: break

            # Simple temporary lockout handling: skip if recently marked as locked
            if username in self.locked_accounts and (time.time() - self.locked_accounts[username]['timestamp'] < self.lockout_resume_delay):
                 self.log_output(f"[i] Skipping '{username}'. Marked as potentially locked. Resuming in {int(self.locked_accounts[username]['timestamp'] + self.lockout_resume_delay - time.time())} seconds.")
                 self.completed_attempts += 1 # Count this as an attempt for progress
                 self.update_progress((self.completed_attempts / self.total_attempts) * 100)
                 continue

            try:
                headers = random.choice(self.fake_headers)
                proxy = self.get_random_proxy()
                data = {user_field: username, pass_field: 'invalidpassword'}
                r = requests.post(url, data=data, headers=headers, proxies=proxy, timeout=10)

                is_locked, lockout_reasons = self._check_lockout_indicators(r)
                if is_locked:
                    self.log_output(f"[!!!] Possible Account Lockout Detected for '{username}'. Indicators: {', '.join(lockout_reasons)}. Marking for temporary skip.")
                    self.locked_accounts[username] = {'reasons': lockout_reasons, 'timestamp': time.time()}
                    self._increase_delay(reason=f"Lockout detected for {username}")
                    time.sleep(self.current_delay)
                    continue # Skip to the next username

                if r.status_code == 429:
                    self.log_output(f"[⚠️] Received 429 Too Many Requests for '{username}'. Increasing delay.")
                    self._increase_delay(reason=f"429 for {username}")
                    time.sleep(self.current_delay)
                    continue
                elif r.status_code == 403:
                    self.log_output(f"[⚠️] Received 403 Forbidden for '{username}'. May indicate block. Increasing delay.")
                    self._increase_delay(reason=f"403 for {username}")
                    time.sleep(self.current_delay)
                    continue

                if "Invalid password" in r.text:
                    self.log_output(f"[!] Possible enumeration: '{username}' recognized (invalid password)")
                    # If a username is recognized, remove it from the locked_accounts list if it was there
                    if username in self.locked_accounts:
                        del self.locked_accounts[username]
                elif "Invalid username" in r.text:
                    self.log_output(f"[ ] Username '{username}' appears invalid.")
                    # If a username is explicitly invalid, remove it from the locked_accounts list
                    if username in self.locked_accounts:
                        del self.locked_accounts[username]
                else:
                    self.log_output(f"[?] Ambiguous response for '{username}'")

            except requests.exceptions.Timeout:
                self.log_output(f"[X] Request timed out for '{username}'. Increasing delay.")
                self._increase_delay(reason=f"Timeout for {username}")
            except requests.exceptions.ConnectionError as e:
                 self.log_output(f"[X] Connection error for '{username}': {e}. Increasing delay.")
                 self._increase_delay(reason=f"Connection error for {username}")
            except Exception as e:
                self.log_output(f"[X] Unexpected error testing '{username}': {e}")
            finally:
                 self.completed_attempts += 1
                 self.update_progress((self.completed_attempts / self.total_attempts) * 100)
                 self._apply_delay()

    def test_weak_passwords(self, url, user_field, pass_field, passwords):
        if not self.is_scanning: return
        self.log_output("\n=== Weak Password Test ===")
        target_username = 'admin' # Or allow user to specify

        # Simple temporary lockout handling for the target username
        if target_username in self.locked_accounts and (time.time() - self.locked_accounts[target_username]['timestamp'] < self.lockout_resume_delay):
             self.log_output(f"[i] Skipping weak password test for '{target_username}'. Marked as potentially locked. Resuming in {int(self.locked_accounts[target_username]['timestamp'] + self.lockout_resume_delay - time.time())} seconds.")
             # Count all passwords as attempts for progress, as we're skipping the whole block
             self.completed_attempts += len(passwords)
             self.update_progress((self.completed_attempts / self.total_attempts) * 100)
             return # Skip the entire weak password test for this user

        for pwd in passwords:
            if not self.is_scanning: break
            try:
                headers = random.choice(self.fake_headers)
                proxy = self.get_random_proxy()
                data = {user_field: target_username, pass_field: pwd}
                r = requests.post(url, data=data, headers=headers, proxies=proxy, timeout=10, allow_redirects=False)

                is_locked, lockout_reasons = self._check_lockout_indicators(r)
                if is_locked:
                    self.log_output(f"[!!!] Possible Account Lockout Detected for '{target_username}'. Indicators: {', '.join(lockout_reasons)}. Marking for temporary skip.")
                    self.locked_accounts[target_username] = {'reasons': lockout_reasons, 'timestamp': time.time()}
                    self._increase_delay(reason=f"Lockout detected for {target_username}")
                    time.sleep(self.current_delay)
                    break # Stop testing passwords for this username

                if r.status_code == 429:
                    self.log_output(f"[⚠️] Received 429 Too Many Requests for password '{pwd}'. Increasing delay.")
                    self._increase_delay(reason=f"429 for password {pwd}")
                    time.sleep(self.current_delay)
                    continue
                elif r.status_code == 403:
                    self.log_output(f"[⚠️] Received 403 Forbidden for password '{pwd}'. May indicate block. Increasing delay.")
                    self._increase_delay(reason=f"403 for password {pwd}")
                    time.sleep(self.current_delay)
                    continue

                if "Welcome" in r.text or r.status_code == 302:
                    self.log_output(f"[!!!] Weak password found: '{pwd}' for user '{target_username}'")
                    # If a weak password is found, remove the user from locked_accounts if it was there
                    if target_username in self.locked_accounts:
                         del self.locked_accounts[target_username]
                    break
            except requests.exceptions.RequestException as e:
                self.log_output(f"[X] Network error trying password '{pwd}': {e}")
            except Exception as e:
                self.log_output(f"[X] Unexpected error trying password '{pwd}': {e}")
            finally:
                 self.completed_attempts += 1
                 self.update_progress((self.completed_attempts / self.total_attempts) * 100)
                 self._apply_delay()


    def check_session_cookies(self, url):
        if not self.is_scanning: return
        self.log_output("\n=== Session Cookie Check ===")
        try:
            session = requests.Session()
            headers = random.choice(self.fake_headers)
            proxy = self.get_random_proxy()
            r = session.get(url, headers=headers, proxies=proxy, timeout=10)
            cookies = session.cookies.get_dict()

            # Check for common rate limit status codes
            if r.status_code == 429:
                 self.log_output("[⚠️] Received 429 Too Many Requests during session check. Increasing delay.")
                 self._increase_delay(reason="429 during session check")
            elif r.status_code == 403:
                 self.log_output("[⚠️] Received 403 Forbidden during session check. Increasing delay.")
                 self._increase_delay(reason="403 during session check")

            if cookies:
                self.log_output(f"[i] Session cookies detected: {cookies}")
                for name in cookies:
                    if 'session' in name.lower():
                        self.log_output(f"[!] Possible session cookie: {name}")
            else:
                self.log_output("[ ] No cookies found.")
        except requests.exceptions.Timeout:
            self.log_output(f"[X] Request timed out during session check. Increasing delay.")
            self._increase_delay(reason="Timeout during session check")
        except requests.exceptions.ConnectionError as e:
             self.log_output(f"[X] Connection error during session check: {e}. Increasing delay.")
             self._increase_delay(reason="Connection error during session check")
        except Exception as e:
            self.log_output(f"[X] Unexpected error checking session cookies: {e}")
        finally:
            self._apply_delay()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Auth Test Module")
    auth_module = AuthTestModule(root)
    auth_module.frame.pack(padx=10, pady=10)
    root.mainloop()
