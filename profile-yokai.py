#!/usr/bin/env python3

import sys
import re
import json
import subprocess
import os
import requests
import csv
import time
import threading
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
from fake_useragent import UserAgent
import cloudscraper
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import sqlite3
import shutil
import signal

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    DIM = '\033[2m'
    ITALIC = '\033[3m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'

    BLACK = '\033[30m'
    DARK_GRAY = '\033[90m'
    LIGHT_GRAY = '\033[37m'
    WHITE = '\033[97m'

    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    ORANGE = '\033[38;5;214m'
    GOLD = '\033[38;5;220m'
    PINK = '\033[38;5;206m'
    PURPLE = '\033[38;5;129m'
    TEAL = '\033[38;5;45m'
    LIME = '\033[38;5;118m'
    CORAL = '\033[38;5;203m'
    SKY = '\033[38;5;117m'
    MINT = '\033[38;5;121m'
    LAVENDER = '\033[38;5;183m'
    PEACH = '\033[38;5;216m'
    MAGENTA = '\033[35m'

    BG_ORANGE = '\033[48;5;214m'
    BG_GOLD = '\033[48;5;220m'
    BG_PINK = '\033[48;5;206m'
    BG_PURPLE = '\033[48;5;129m'
    BG_TEAL = '\033[48;5;45m'

class Icons:
    SPARKLE = "✦"
    STAR = "★"
    HEART = "♥"
    DIAMOND = "♦"
    CLUB = "♣"
    SPADE = "♠"
    MUSIC = "♫"
    SUN = "☀"
    MOON = "☽"
    CLOUD = "☁"
    UMBRELLA = "☂"
    SNOW = "❄"
    FIRE = "🔥"
    WATER = "💧"
    LEAF = "🌿"
    FLOWER = "🌸"
    CROWN = "👑"
    GEM = "💎"
    ROCKET = "🚀"
    STAR2 = "⭐"
    LIGHTNING = "⚡"
    GEAR = "⚙"
    WARNING = "⚠"
    CHECK = "✓"
    CROSS = "✗"
    ARROW = "➜"
    DOUBLE_ARROW = "➤"
    BULLET = "•"
    DOT = "․"
    LINE = "━"
    DOUBLE_LINE = "═"
    THIN_LINE = "─"
    CORNER = "┐"
    CORNER2 = "┘"
    CORNER3 = "┌"
    CORNER4 = "└"
    PIPE = "│"
    PIPE2 = "┃"
    BOX_TOP = "┌─"
    BOX_BOTTOM = "└─"
    BOX_LEFT = "├─"
    BOX_RIGHT = "─┤"
    BOX_CROSS = "┼─"
    SEARCH = "🔍"
    BOOK = "📖"
    USERS = "👥"
    TIME = "⏱"

class ProgressBar:
    def __init__(self, total, width=50, fill_char='█', empty_char='░', color=Colors.GREEN):
        self.total = total
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.color = color
        self.current = 0
        self.start_time = time.time()

    def update(self, current, message=""):
        self.current = min(current, self.total)
        percent = (self.current / self.total) * 100
        filled = int(self.width * self.current / self.total)
        empty = self.width - filled

        bar = f"{self.color}{self.fill_char * filled}{Colors.DIM}{self.empty_char * empty}{Colors.END}"

        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {int(eta)}s" if eta < 3600 else f"ETA: {int(eta/60)}m"
        else:
            eta_str = "ETA: ---"

        sys.stdout.write(f"\r{Colors.CYAN}{Icons.ARROW}{Colors.END} {bar} {Colors.GOLD}{percent:6.1f}%{Colors.END} [{self.current}/{self.total}] {Colors.DIM}{eta_str}{Colors.END} {message}")
        sys.stdout.flush()

    def finish(self, message="Complete!"):
        self.update(self.total, f"{Colors.GREEN}{Icons.CHECK} {message}{Colors.END}")
        print()

class Spinner:
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def spin(self):
        idx = 0
        while self.running:
            sys.stdout.write(f"\r{Colors.CYAN}{self.frames[idx % len(self.frames)]}{Colors.END} {Colors.DIM}{self.message}...{Colors.END}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, success=True):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        if success:
            sys.stdout.write(f"\r{Colors.GREEN}{Icons.CHECK}{Colors.END} {Colors.DIM}{self.message}...{Colors.END} {Colors.GREEN}Done{Colors.END}\n")
        else:
            sys.stdout.write(f"\r{Colors.RED}{Icons.CROSS}{Colors.END} {Colors.DIM}{self.message}...{Colors.END} {Colors.RED}Failed{Colors.END}\n")
        sys.stdout.flush()

class AnimatedBorder:
    @staticmethod
    def box(text, color=Colors.CYAN, width=None):
        lines = text.split('\n')
        max_len = max(len(line) for line in lines)
        if width:
            max_len = max(max_len, width - 4)

        top = f"{color}{Icons.BOX_TOP}{Icons.THIN_LINE * (max_len + 2)}{Icons.CORNER}{Colors.END}"
        bottom = f"{color}{Icons.BOX_BOTTOM}{Icons.THIN_LINE * (max_len + 2)}{Icons.CORNER2}{Colors.END}"

        result = [top]
        for line in lines:
            padding = max_len - len(line)
            result.append(f"{color}{Icons.PIPE}{Colors.END} {line}{' ' * padding} {color}{Icons.PIPE}{Colors.END}")
        result.append(bottom)

        return '\n'.join(result)

    @staticmethod
    def divider(char='━', color=Colors.DIM):
        try:
            width = os.get_terminal_size().columns
        except:
            width = 80
        return f"{color}{char * width}{Colors.END}"

class TableFormatter:
    @staticmethod
    def create_table(headers, rows, colors=None):
        if not rows:
            return "No data available"

        if not colors:
            colors = [Colors.CYAN] * len(headers)

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        total_width = sum(col_widths) + (len(headers) * 3) + 1

        top = f"{Colors.DIM}{Icons.CORNER3}{Icons.THIN_LINE * (total_width - 2)}{Icons.CORNER}{Colors.END}"
        bottom = f"{Colors.DIM}{Icons.CORNER4}{Icons.THIN_LINE * (total_width - 2)}{Icons.CORNER2}{Colors.END}"

        result = [top]

        header_line = " "
        for i, header in enumerate(headers):
            header_line += f" {colors[i % len(colors)]}{Colors.BOLD}{header.center(col_widths[i])}{Colors.END} "
        result.append(header_line)

        sep = f"{Colors.DIM}{Icons.BOX_LEFT}{Icons.THIN_LINE * (total_width - 2)}{Icons.BOX_RIGHT}{Colors.END}"
        result.append(sep)

        for row in rows:
            line = " "
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    cell_str = str(cell)
                    color = colors[i % len(colors)] if i < len(colors) else Colors.WHITE
                    line += f" {color}{cell_str.ljust(col_widths[i])}{Colors.END} "
            result.append(line)

        result.append(bottom)
        return '\n'.join(result)

class GradientText:
    @staticmethod
    def rainbow(text):
        colors = [Colors.RED, Colors.ORANGE, Colors.GOLD, Colors.GREEN, Colors.CYAN, Colors.BLUE, Colors.PURPLE]
        result = ""
        for i, char in enumerate(text):
            if char == ' ':
                result += ' '
            else:
                result += colors[i % len(colors)] + char + Colors.END
        return result

    @staticmethod
    def fire(text):
        colors = [Colors.RED, Colors.ORANGE, Colors.GOLD, Colors.YELLOW]
        result = ""
        for i, char in enumerate(text):
            if char == ' ':
                result += ' '
            else:
                color_idx = min(i // 2, len(colors) - 1)
                result += colors[color_idx] + char + Colors.END
        return result

    @staticmethod
    def ocean(text):
        colors = [Colors.TEAL, Colors.CYAN, Colors.BLUE, Colors.PURPLE]
        result = ""
        for i, char in enumerate(text):
            if char == ' ':
                result += ' '
            else:
                result += colors[i % len(colors)] + char + Colors.END
        return result

class ColorUtils:
    @staticmethod
    def success(text):
        return f"{Colors.GREEN}{Icons.CHECK} {text}{Colors.END}"

    @staticmethod
    def error(text):
        return f"{Colors.RED}{Icons.CROSS} {text}{Colors.END}"

    @staticmethod
    def warning(text):
        return f"{Colors.YELLOW}{Icons.WARNING} {text}{Colors.END}"

    @staticmethod
    def info(text):
        return f"{Colors.CYAN}{Icons.ARROW} {text}{Colors.END}"

    @staticmethod
    def highlight(text, color=Colors.GOLD):
        return f"{color}{Colors.BOLD}{text}{Colors.END}"

    @staticmethod
    def dim(text):
        return f"{Colors.DIM}{text}{Colors.END}"

class UserAgentRotator:
    def __init__(self):
        try:
            self.ua = UserAgent()
            self.custom_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
                "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            ]
            self.current_index = 0
        except:
            self.ua = None

    def get_random(self):
        if self.ua:
            try:
                return self.ua.random
            except:
                return random.choice(self.custom_agents)
        return random.choice(self.custom_agents)

    def get_rotating(self):
        agent = self.custom_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.custom_agents)
        return agent

class RequestManager:
    def __init__(self, use_tor=False, proxy=None, max_retries=3):
        self.session = requests.Session()
        self.user_agent_rotator = UserAgentRotator()
        self.use_tor = use_tor
        self.proxy = proxy
        self.max_retries = max_retries

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.setup_proxy()

    def setup_proxy(self):
        if self.use_tor:
            self.session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
        elif self.proxy:
            self.session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }

    def get_headers(self):
        return {
            "User-Agent": self.user_agent_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    def get(self, url, timeout=30, use_cloudscraper=False):
        headers = self.get_headers()

        if use_cloudscraper:
            scraper = cloudscraper.create_scraper()
            return scraper.get(url, headers=headers, timeout=timeout)

        return self.session.get(url, headers=headers, timeout=timeout)

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_cache_key(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def get_cached(self, url, max_age=3600):
        cache_key = self.get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, cache_key)

        if os.path.exists(cache_file):
            age = time.time() - os.path.getmtime(cache_file)
            if age < max_age:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        return None

    def set_cached(self, url, data):
        cache_key = self.get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, cache_key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            pass

class RateLimiter:
    def __init__(self, requests_per_second=1):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < (1.0 / self.requests_per_second):
                time.sleep((1.0 / self.requests_per_second) - time_since_last)
            self.last_request_time = time.time()

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.lock = threading.Lock()

    def load_proxies_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            print(ColorUtils.success(f"Loaded {len(self.proxies)} proxies"))
            return True
        except:
            print(ColorUtils.error(f"Failed to load proxies from {filename}"))
            return False

    def get_next_proxy(self):
        with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.request_manager = RequestManager()
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiter(requests_per_second=2)
        self.proxy_manager = ProxyManager()
        self.stats = {
            'requests': 0,
            'success': 0,
            'failures': 0,
            'cached_hits': 0
        }
        self.lock = threading.Lock()
        self.running = True

    def get_session(self, use_tor=False, proxy=None):
        session_key = f"tor_{use_tor}_proxy_{proxy}"
        if session_key not in self.sessions:
            self.sessions[session_key] = RequestManager(use_tor=use_tor, proxy=proxy)
        return self.sessions[session_key]

    def request(self, url, use_cache=True, cache_age=3600, use_tor=False, proxy=None, use_cloudscraper=False):
        with self.lock:
            self.stats['requests'] += 1

        if use_cache:
            cached_data = self.cache_manager.get_cached(url, cache_age)
            if cached_data:
                with self.lock:
                    self.stats['cached_hits'] += 1
                return cached_data

        self.rate_limiter.wait()

        session = self.get_session(use_tor=use_tor, proxy=proxy)

        for attempt in range(self.request_manager.max_retries):
            try:
                response = session.get(url, use_cloudscraper=use_cloudscraper)
                response.raise_for_status()

                with self.lock:
                    self.stats['success'] += 1

                if use_cache and response.status_code == 200:
                    try:
                        data = response.json()
                        self.cache_manager.set_cached(url, data)
                        return data
                    except:
                        return response.text

                return response
            except Exception as e:
                if attempt == self.request_manager.max_retries - 1:
                    with self.lock:
                        self.stats['failures'] += 1
                    raise e
                time.sleep(2 ** attempt)

    def get_stats(self):
        with self.lock:
            return self.stats.copy()

    def stop(self):
        self.running = False

class DatabaseManager:
    def __init__(self, db_file="profile_yokai.db"):
        self.db_file = db_file
        try:
            self.conn = sqlite3.connect(db_file)
            self.cursor = self.conn.cursor()
            self.create_tables()
        except:
            print(ColorUtils.warning("SQLite not available, using JSON storage"))
            self.conn = None

    def create_tables(self):
        if not self.conn:
            return

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT,
                followers INTEGER,
                following INTEGER,
                stories INTEGER,
                verified INTEGER,
                data JSON,
                last_updated TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY,
                username TEXT,
                title TEXT,
                parts INTEGER,
                reads INTEGER,
                votes INTEGER,
                data JSON,
                last_updated TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring (
                username TEXT,
                timestamp TIMESTAMP,
                followers INTEGER,
                following INTEGER,
                stories INTEGER,
                PRIMARY KEY (username, timestamp)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                status TEXT,
                error TEXT,
                timestamp TIMESTAMP
            )
        ''')

        self.conn.commit()

    def save_user(self, username, data):
        if not self.conn:
            return False

        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users
                (username, name, followers, following, stories, verified, data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                data.get('name', ''),
                int(data.get('numFollowers', 0)),
                int(data.get('numFollowing', 0)),
                int(data.get('numStoriesPublished', 0)),
                1 if data.get('verified', False) else 0,
                json.dumps(data),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except:
            return False

    def save_story(self, story_id, username, data):
        if not self.conn:
            return False

        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO stories
                (id, username, title, parts, reads, votes, data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                story_id,
                username,
                data.get('title', ''),
                int(data.get('numParts', 0)),
                int(data.get('readCount', 0)),
                int(data.get('voteCount', 0)),
                json.dumps(data),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except:
            return False

    def save_monitoring(self, username, data):
        if not self.conn:
            return False

        try:
            self.cursor.execute('''
                INSERT INTO monitoring (username, timestamp, followers, following, stories)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                username,
                datetime.now().isoformat(),
                int(data.get('numFollowers', 0)),
                int(data.get('numFollowing', 0)),
                int(data.get('numStoriesPublished', 0))
            ))
            self.conn.commit()
            return True
        except:
            return False

    def get_user_history(self, username, limit=10):
        if not self.conn:
            return []

        try:
            self.cursor.execute('''
                SELECT timestamp, followers, following, stories
                FROM monitoring
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (username, limit))
            return self.cursor.fetchall()
        except:
            return []

    def get_all_users(self):
        if not self.conn:
            return []

        try:
            self.cursor.execute('SELECT username, name, followers, following, stories, verified, last_updated FROM users ORDER BY followers DESC')
            return self.cursor.fetchall()
        except:
            return []

    def get_user(self, username):
        if not self.conn:
            return None

        try:
            self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            return self.cursor.fetchone()
        except:
            return None

    def log_batch_job(self, username, status, error=None):
        if not self.conn:
            return

        try:
            self.cursor.execute('''
                INSERT INTO batch_jobs (username, status, error, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (username, status, error, datetime.now().isoformat()))
            self.conn.commit()
        except:
            pass

def check_dependencies():
    missing_deps = []

    for cmd in ["curl", "jq", "sed"]:
        try:
            subprocess.run([cmd, "--version"], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append(cmd)

    try:
        import fake_useragent
    except ImportError:
        missing_deps.append("fake_useragent")

    try:
        import cloudscraper
    except ImportError:
        missing_deps.append("cloudscraper")

    if missing_deps:
        print(ColorUtils.error(f"Missing dependencies: {', '.join(missing_deps)}"))
        print(ColorUtils.info("Install with: pip install fake_useragent cloudscraper"))
        if "curl" in missing_deps or "jq" in missing_deps or "sed" in missing_deps:
            print(ColorUtils.info("On Termux: pkg install curl jq sed"))
        sys.exit(1)

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def reset_environment():
    clear_screen()

    banner = f"""
{Colors.RED}╔═══════════════════════════════════════════════════════════════════════════════╗
{Colors.RED}║{Colors.ORANGE}  {GradientText.fire('🔥  P R O F I L E   Y O K A I  🔥')}                                          {Colors.RED}║
{Colors.RED}║{Colors.GOLD}  {GradientText.rainbow('👻  The Mysterious Spirit of Wattpad  👻')}                                   {Colors.RED}║
{Colors.RED}╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.BLUE}╔═══════════════════════════════════════════════════════════════════════════════╗
{Colors.BLUE}║{Colors.PINK}  {GradientText.ocean('⚡  Author: SYLHETYHACKVENGER (THE-ERROR808)  ⚡')}                                  {Colors.BLUE}║
{Colors.BLUE}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)

session_manager = SessionManager()
db_manager = DatabaseManager()
monitoring_active = False

def signal_handler(sig, frame):
    global monitoring_active
    print(f"\n{Colors.YELLOW}╔═══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Colors.YELLOW}║{Colors.ORANGE}  {Icons.WARNING}  Interrupt received, cleaning up...{Colors.YELLOW}                                  ║")
    print(f"{Colors.YELLOW}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
    monitoring_active = False
    session_manager.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def validate_username(username):
    if not username or len(username) < 3:
        return False
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False
    return True

def extract_profile_data(username, return_raw=False, use_cache=True, use_tor=False, proxy=None):
    if not validate_username(username):
        print(ColorUtils.error("Invalid username format"))
        return None

    target_url = f"https://www.wattpad.com/user/{username}/about"

    if not return_raw:
        print(f"\n{Colors.CYAN}{Icons.ARROW}{Colors.END} {Colors.DIM}Scraping Wattpad user data for{Colors.END} {Colors.GOLD}@{username}{Colors.END}\n")

    spinner = Spinner(f"Fetching data for {username}")
    spinner.start()

    try:
        response = session_manager.request(
            target_url,
            use_cache=use_cache,
            use_tor=use_tor,
            proxy=proxy,
            use_cloudscraper=True
        )

        if isinstance(response, dict):
            html_source = json.dumps(response)
        elif hasattr(response, 'text'):
            html_source = response.text
        else:
            html_source = str(response)

    except Exception as e:
        spinner.stop(False)
        if not return_raw:
            print(ColorUtils.error(f"Network connectivity failed: {e}"))
        return None

    html_no_newlines = html_source.replace('\n', '')
    json_match = re.search(r'window\.prefetched\s*=\s*(\{.*?\});', html_no_newlines)

    if not json_match:
        json_match = re.search(r'<script[^>]*>window\.prefetched\s*=\s*(\{.*?\});</script>', html_no_newlines)

    if not json_match:
        spinner.stop(False)
        if not return_raw:
            print(ColorUtils.error("Failed to extract source payload block. Verify username."))
        return None

    json_blob = json_match.group(1)

    try:
        data = json.loads(json_blob)
    except json.JSONDecodeError as e:
        spinner.stop(False)
        if not return_raw:
            print(ColorUtils.error(f"Failed to parse JSON payload: {e}"))
        return None

    user_key = f"user.{username}"
    if user_key not in data or not data[user_key].get('data'):
        spinner.stop(False)
        if not return_raw:
            print(ColorUtils.error("Unexpected payload schema encountered."))
        return None

    profile = data[user_key]['data'][0]
    spinner.stop(True)

    if return_raw:
        return profile

    def get_field(field_path):
        parts = field_path.split('.')
        current = profile
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return f"{Colors.DIM}N/A{Colors.END}"

        if current is None:
            return f"{Colors.DIM}N/A{Colors.END}"
        return str(current)

    print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Colors.CYAN}║{Colors.GOLD}  {Icons.STAR}  {Colors.BOLD}Profile Information Summary{Colors.END}{Colors.GOLD}  {Icons.STAR}  {Colors.CYAN}                                             ║")
    print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}\n")

    fields = [
        ("Username", get_field('username'), Colors.PINK),
        ("Avatar", get_field('avatar'), Colors.SKY),
        ("Private", get_field('isPrivate'), Colors.YELLOW),
        ("Name", get_field('name'), Colors.CYAN),
        ("First Name", get_field('firstName'), Colors.TEAL),
        ("Last Name", get_field('lastName'), Colors.TEAL),
        ("Description", get_field('description'), Colors.DIM),
        ("Gender", get_field('gender'), Colors.MAGENTA),
        ("Location", get_field('location'), Colors.ORANGE),
        ("Created", get_field('createDate'), Colors.DIM),
        ("Verified", get_field('verified'), Colors.GREEN),
        ("Ambassador", get_field('ambassador'), Colors.PURPLE),
        ("Followers", get_field('numFollowers'), Colors.GOLD),
        ("Following", get_field('numFollowing'), Colors.CYAN),
        ("Stories Published", get_field('numStoriesPublished'), Colors.LIME),
        ("Reading Lists", get_field('numLists'), Colors.BLUE)
    ]

    for label, value, color in fields:
        print(f"  {Colors.DIM}{Icons.DOT}{Colors.END} {Colors.BOLD}{label}:{Colors.END} {color}{value}{Colors.END}")

    print(f"\n{Colors.CYAN}{Icons.ARROW}{Colors.END} {Colors.DIM}URL:{Colors.END} {Colors.GOLD}https://www.wattpad.com/user/{username}/{Colors.END}")
    print(f"{Colors.CYAN}{Icons.SPARKLE}{Colors.END} {Colors.DIM}Profile Yokai has revealed the data{Colors.END}\n")

    db_manager.save_user(username, profile)

    stats = session_manager.get_stats()
    print(f"{Colors.DIM}┌─{Icons.THIN_LINE * 60}─┐{Colors.END}")
    print(f"{Colors.DIM}│{Colors.END} {Colors.CYAN}{Icons.GEAR}{Colors.END} {Colors.DIM}Requests:{Colors.END} {Colors.WHITE}{stats['requests']}{Colors.END}  {Colors.DIM}Success:{Colors.END} {Colors.GREEN}{stats['success']}{Colors.END}  {Colors.DIM}Failures:{Colors.END} {Colors.RED}{stats['failures']}{Colors.END}  {Colors.DIM}Cached:{Colors.END} {Colors.GOLD}{stats['cached_hits']}{Colors.END} {Colors.DIM}│{Colors.END}")
    print(f"{Colors.DIM}└─{Icons.THIN_LINE * 60}─┘{Colors.END}\n")

    return profile

def export_to_json(profile_data, username):
    if not profile_data:
        print(ColorUtils.error("No data to export"))
        return False

    filename = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    spinner = Spinner(f"Exporting to {filename}")
    spinner.start()

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        spinner.stop(True)
        print(ColorUtils.success(f"Exported to {filename}"))
        return True
    except Exception as e:
        spinner.stop(False)
        print(ColorUtils.error(f"Failed to export: {e}"))
        return False

def export_to_csv(profile_data, username):
    if not profile_data:
        print(ColorUtils.error("No data to export"))
        return False

    filename = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    spinner = Spinner(f"Exporting to {filename}")
    spinner.start()

    try:
        flat_data = {}
        def flatten_dict(d, parent_key=''):
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    flatten_dict(v, new_key)
                else:
                    flat_data[new_key] = v

        flatten_dict(profile_data)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            writer.writeheader()
            writer.writerow(flat_data)
        spinner.stop(True)
        print(ColorUtils.success(f"Exported to {filename}"))
        return True
    except Exception as e:
        spinner.stop(False)
        print(ColorUtils.error(f"Failed to export: {e}"))
        return False

def extract_stories_data(username, limit=10, use_cache=True, use_tor=False, proxy=None):
    if not validate_username(username):
        return []

    stories = []
    offset = 0
    spinner = Spinner(f"Fetching stories for {username}")
    spinner.start()

    while len(stories) < limit:
        url = f"https://www.wattpad.com/api/v3/users/{username}/stories?offset={offset}&limit={min(10, limit - len(stories))}"

        try:
            response = session_manager.request(
                url,
                use_cache=use_cache,
                use_tor=use_tor,
                proxy=proxy
            )

            if isinstance(response, dict):
                data = response
            else:
                data = response.json()

            if 'stories' in data and data['stories']:
                for story in data['stories']:
                    stories.append(story)
                    db_manager.save_story(story.get('id'), username, story)
                    if len(stories) >= limit:
                        break
                offset += len(data['stories'])
            else:
                break

        except Exception as e:
            spinner.stop(False)
            print(ColorUtils.warning(f"Error fetching stories at offset {offset}: {e}"))
            break

    spinner.stop(True)
    return stories

def extract_followers_data(username, limit=100, use_cache=True, use_tor=False, proxy=None):
    if not validate_username(username):
        return []

    followers = []
    cursor = None
    spinner = Spinner(f"Fetching followers for {username}")
    spinner.start()

    while len(followers) < limit:
        url = f"https://www.wattpad.com/api/v3/users/{username}/followers?limit={min(25, limit - len(followers))}"
        if cursor:
            url += f"&cursor={cursor}"

        try:
            response = session_manager.request(
                url,
                use_cache=use_cache,
                use_tor=use_tor,
                proxy=proxy
            )

            if isinstance(response, dict):
                data = response
            else:
                data = response.json()

            if 'users' in data and data['users']:
                for user in data['users']:
                    followers.append(user)
                    if len(followers) >= limit:
                        break

                if 'next' in data and data['next'] and len(followers) < limit:
                    cursor = data['next'].split('cursor=')[-1]
                else:
                    break
            else:
                break

        except Exception as e:
            spinner.stop(False)
            print(ColorUtils.warning(f"Error fetching followers: {e}"))
            break

    spinner.stop(True)
    return followers

def extract_following_data(username, limit=100, use_cache=True, use_tor=False, proxy=None):
    if not validate_username(username):
        return []

    following = []
    cursor = None
    spinner = Spinner(f"Fetching following for {username}")
    spinner.start()

    while len(following) < limit:
        url = f"https://www.wattpad.com/api/v3/users/{username}/following?limit={min(25, limit - len(following))}"
        if cursor:
            url += f"&cursor={cursor}"

        try:
            response = session_manager.request(
                url,
                use_cache=use_cache,
                use_tor=use_tor,
                proxy=proxy
            )

            if isinstance(response, dict):
                data = response
            else:
                data = response.json()

            if 'users' in data and data['users']:
                for user in data['users']:
                    following.append(user)
                    if len(following) >= limit:
                        break

                if 'next' in data and data['next'] and len(following) < limit:
                    cursor = data['next'].split('cursor=')[-1]
                else:
                    break
            else:
                break

        except Exception as e:
            spinner.stop(False)
            print(ColorUtils.warning(f"Error fetching following: {e}"))
            break

    spinner.stop(True)
    return following

def search_users(query, limit=20, use_cache=True, use_tor=False, proxy=None):
    if not query or len(query) < 2:
        print(ColorUtils.error("Search query too short"))
        return []

    spinner = Spinner(f"Searching for '{query}'")
    spinner.start()

    url = f"https://www.wattpad.com/api/v3/search/users?query={query}&limit={limit}"

    try:
        response = session_manager.request(
            url,
            use_cache=use_cache,
            use_tor=use_tor,
            proxy=proxy
        )

        if isinstance(response, dict):
            data = response
        else:
            data = response.json()

        spinner.stop(True)
        return data.get('users', [])
    except Exception as e:
        spinner.stop(False)
        print(ColorUtils.error(f"Search failed: {e}"))
        return []

def monitor_users(username, interval=3600, duration=86400, use_tor=False, proxy=None):
    global monitoring_active

    if not validate_username(username):
        print(ColorUtils.error("Invalid username"))
        return

    monitoring_active = True

    print(f"\n{Colors.GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Colors.GREEN}║{Colors.GOLD}  {Icons.MOON}  {Colors.BOLD}Monitoring {Colors.END}{Colors.PINK}@{username}{Colors.GOLD}  {Icons.MOON}  {Colors.GREEN}                                                       ║")
    print(f"{Colors.GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
    print(f"{Colors.DIM}  Duration: {duration}s  |  Interval: {interval}s  |  {Icons.WARNING} Press Ctrl+C to stop{Colors.END}\n")

    start_time = time.time()
    last_data = None

    try:
        while monitoring_active and (time.time() - start_time) < duration:
            try:
                spinner = Spinner(f"Checking {username}")
                spinner.start()

                profile = extract_profile_data(username, return_raw=True, use_cache=False, use_tor=use_tor, proxy=proxy)
                spinner.stop(True)

                if profile:
                    db_manager.save_monitoring(username, profile)

                    followers = profile.get('numFollowers', 0)
                    following = profile.get('numFollowing', 0)
                    stories = profile.get('numStoriesPublished', 0)

                    if last_data:
                        follower_change = followers - last_data.get('numFollowers', 0)
                        following_change = following - last_data.get('numFollowing', 0)
                        stories_change = stories - last_data.get('numStoriesPublished', 0)

                        change_parts = []
                        if follower_change != 0:
                            color = Colors.GREEN if follower_change > 0 else Colors.RED
                            change_parts.append(f"{color}{follower_change:+d}{Colors.END}")
                        if following_change != 0:
                            color = Colors.GREEN if following_change > 0 else Colors.RED
                            change_parts.append(f"{color}{following_change:+d}{Colors.END}")
                        if stories_change != 0:
                            color = Colors.GREEN if stories_change > 0 else Colors.RED
                            change_parts.append(f"{color}{stories_change:+d}{Colors.END}")

                        change_str = f" ({', '.join(change_parts)})" if change_parts else ""
                    else:
                        change_str = ""

                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{Colors.DIM}{Icons.DOT}{Colors.END} {Colors.GREEN}[{timestamp}]{Colors.END} {Colors.CYAN}Followers:{Colors.END} {Colors.WHITE}{followers:,}{Colors.END}  {Colors.CYAN}Following:{Colors.END} {Colors.WHITE}{following:,}{Colors.END}  {Colors.CYAN}Stories:{Colors.END} {Colors.WHITE}{stories}{Colors.END}{change_str}")
                    last_data = profile

                if monitoring_active:
                    remaining = int(interval)
                    bar = ProgressBar(remaining, width=30)
                    for i in range(remaining, 0, -1):
                        if not monitoring_active:
                            break
                        bar.update(remaining - i + 1, f"{Colors.DIM}Next check in {i}s{Colors.END}")
                        time.sleep(1)
                    print()

            except Exception as e:
                print(ColorUtils.error(f"Monitoring error: {e}"))
                if monitoring_active:
                    time.sleep(60)

    except KeyboardInterrupt:
        pass
    finally:
        monitoring_active = False
        print(f"\n{Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}Monitoring stopped{Colors.END}\n")

def show_dashboard():
    reset_environment()

    print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Colors.CYAN}║{Colors.GOLD}  {Icons.GEM}  {Colors.BOLD}Profile Yokai Dashboard{Colors.END}{Colors.GOLD}  {Icons.GEM}  {Colors.CYAN}                                               ║")
    print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}\n")

    users = db_manager.get_all_users()
    if not users:
        print(f"{Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}No users in database{Colors.END}\n")
        return

    total_followers = sum(user[2] for user in users)
    total_stories = sum(user[4] for user in users)
    verified_count = sum(1 for user in users if user[5])

    print(f"{Colors.CYAN}┌─{Icons.THIN_LINE * 60}─┐{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END} {Colors.GOLD}{Icons.STAR}{Colors.END} {Colors.BOLD}Statistics{Colors.END}{' ' * 46}{Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}├─{Icons.THIN_LINE * 60}─┤{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END}   {Colors.DIM}Total Users:{Colors.END} {Colors.WHITE}{len(users):>6}{Colors.END} {' ' * 43}{Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END}   {Colors.DIM}Total Followers:{Colors.END} {Colors.WHITE}{total_followers:>6,}{Colors.END} {' ' * 37}{Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END}   {Colors.DIM}Total Stories:{Colors.END} {Colors.WHITE}{total_stories:>6,}{Colors.END} {' ' * 39}{Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END}   {Colors.DIM}Verified Users:{Colors.END} {Colors.WHITE}{verified_count:>6}{Colors.END} {' ' * 38}{Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}└─{Icons.THIN_LINE * 60}─┘{Colors.END}\n")

    headers = ["Username", "Name", "Followers", "Stories", "Verified"]
    rows = []
    for user in users[:10]:
        username, name, followers, following, stories, verified, last_updated = user
        verified_str = f"{Colors.GREEN}{Icons.CHECK}{Colors.END}" if verified else f"{Colors.DIM}{Icons.CROSS}{Colors.END}"
        rows.append([f"{Colors.CYAN}{username}{Colors.END}", f"{Colors.DIM}{name[:18]}{Colors.END}", f"{Colors.GOLD}{followers:,}{Colors.END}", f"{Colors.WHITE}{stories}{Colors.END}", verified_str])

    print(TableFormatter.create_table(headers, rows, [Colors.CYAN, Colors.DIM, Colors.GOLD, Colors.WHITE, Colors.GREEN]))

    stats = session_manager.get_stats()
    print(f"\n{Colors.DIM}┌─{Icons.THIN_LINE * 60}─┐{Colors.END}")
    print(f"{Colors.DIM}│{Colors.END} {Colors.CYAN}{Icons.GEAR}{Colors.END} {Colors.DIM}Requests:{Colors.END} {Colors.WHITE}{stats['requests']}{Colors.END}  {Colors.DIM}Success:{Colors.END} {Colors.GREEN}{stats['success']}{Colors.END}  {Colors.DIM}Failures:{Colors.END} {Colors.RED}{stats['failures']}{Colors.END}  {Colors.DIM}Cached:{Colors.END} {Colors.GOLD}{stats['cached_hits']}{Colors.END} {Colors.DIM}│{Colors.END}")
    print(f"{Colors.DIM}└─{Icons.THIN_LINE * 60}─┘{Colors.END}\n")

def batch_process(filename, use_cache=True, use_tor=False, proxy=None, max_workers=5):
    try:
        with open(filename, 'r') as f:
            usernames = [line.strip() for line in f if line.strip() and validate_username(line.strip())]

        if not usernames:
            print(ColorUtils.error(f"No valid usernames found in {filename}"))
            return

        print(f"\n{Colors.GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Colors.GREEN}║{Colors.GOLD}  {Icons.GEAR}  {Colors.BOLD}Batch Processing{Colors.END}{Colors.GOLD}  {Icons.GEAR}  {Colors.GREEN}                                                 ║")
        print(f"{Colors.GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.DIM}  Users: {len(usernames)}  |  Workers: {max_workers}  |  {Icons.WARNING} Press Ctrl+C to cancel{Colors.END}\n")

        results = []
        failed = []

        def process_user(username):
            try:
                profile = extract_profile_data(
                    username,
                    return_raw=True,
                    use_cache=use_cache,
                    use_tor=use_tor,
                    proxy=proxy
                )
                if profile:
                    db_manager.save_user(username, profile)
                    db_manager.log_batch_job(username, "success")
                    return (username, True, None)
                else:
                    db_manager.log_batch_job(username, "failed", "No profile data")
                    return (username, False, "No profile data")
            except Exception as e:
                db_manager.log_batch_job(username, "failed", str(e))
                return (username, False, str(e))

        bar = ProgressBar(len(usernames), width=40)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_user = {executor.submit(process_user, username): username for username in usernames}

            for i, future in enumerate(as_completed(future_to_user), 1):
                username, success, error = future.result()
                if success:
                    results.append(username)
                    status = f"{Colors.GREEN}{Icons.CHECK}{Colors.END}"
                else:
                    failed.append((username, error))
                    status = f"{Colors.RED}{Icons.CROSS}{Colors.END}"

                bar.update(i, f"{status} {Colors.DIM}{username}{Colors.END}")

        print()
        print(f"{Colors.CYAN}┌─{Icons.THIN_LINE * 60}─┐{Colors.END}")
        print(f"{Colors.CYAN}│{Colors.END} {Colors.GREEN}Successful:{Colors.END} {Colors.WHITE}{len(results)}{Colors.END}  {Colors.RED}Failed:{Colors.END} {Colors.WHITE}{len(failed)}{Colors.END}  {Colors.GOLD}Total:{Colors.END} {Colors.WHITE}{len(usernames)}{Colors.END}{' ' * 29}{Colors.CYAN}│{Colors.END}")
        print(f"{Colors.CYAN}└─{Icons.THIN_LINE * 60}─┘{Colors.END}")

        if failed:
            print(f"\n{Colors.YELLOW}Failed users:{Colors.END}")
            for username, error in failed:
                print(f"  {Colors.RED}{Icons.CROSS}{Colors.END} {Colors.DIM}{username}:{Colors.END} {error}")
        print()

    except Exception as e:
        print(ColorUtils.error(f"Batch processing failed: {e}"))

def show_help():
    banner = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗
{Colors.CYAN}║{Colors.GOLD}  {GradientText.rainbow('✦  P R O F I L E   Y O K A I  ✦')}                                      {Colors.CYAN}║
{Colors.CYAN}║{Colors.PINK}  {GradientText.ocean('⚡  Wattpad Profile Scraper  ⚡')}                                         {Colors.CYAN}║
{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)

    print(f"{Colors.BOLD}{Colors.WHITE}Usage:{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END}                {Colors.DIM}- Scrape user profile{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--json{Colors.END}         {Colors.DIM}- Export to JSON{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--csv{Colors.END}          {Colors.DIM}- Export to CSV{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--stories{Colors.END}      {Colors.DIM}- Fetch user stories{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--followers{Colors.END}    {Colors.DIM}- Fetch followers{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--following{Colors.END}    {Colors.DIM}- Fetch following{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}<username>{Colors.END} {Colors.GREEN}--monitor{Colors.END}      {Colors.DIM}- Monitor user changes{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--search{Colors.END} {Colors.GOLD}<query>{Colors.END}          {Colors.DIM}- Search users{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--dashboard{Colors.END}               {Colors.DIM}- Show dashboard{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--batch{Colors.END} {Colors.GOLD}<file>{Colors.END}            {Colors.DIM}- Batch process users{Colors.END}")
    print(f"  {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--help{Colors.END}                    {Colors.DIM}- Show this help{Colors.END}")

    print(f"\n{Colors.BOLD}{Colors.WHITE}Options:{Colors.END}")
    print(f"  {Colors.GREEN}--tor{Colors.END}                                   {Colors.DIM}- Use Tor proxy{Colors.END}")
    print(f"  {Colors.GREEN}--proxy{Colors.END} {Colors.GOLD}<proxy>{Colors.END}                         {Colors.DIM}- Use custom proxy (http://ip:port){Colors.END}")
    print(f"  {Colors.GREEN}--no-cache{Colors.END}                              {Colors.DIM}- Disable cache{Colors.END}")
    print(f"  {Colors.GREEN}--limit{Colors.END} {Colors.GOLD}<number>{Colors.END}                        {Colors.DIM}- Limit results (default: 10){Colors.END}")
    print(f"  {Colors.GREEN}--workers{Colors.END} {Colors.GOLD}<number>{Colors.END}                      {Colors.DIM}- Workers for batch (default: 5){Colors.END}")

    print(f"\n{Colors.BOLD}{Colors.WHITE}Examples:{Colors.END}")
    print(f"  {Colors.DIM}$ {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}wattpad_user{Colors.END} {Colors.GREEN}--json{Colors.END}")
    print(f"  {Colors.DIM}$ {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GOLD}wattpad_user{Colors.END} {Colors.GREEN}--followers --limit 50{Colors.END}")
    print(f"  {Colors.DIM}$ {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--search{Colors.END} {Colors.GOLD}'fantasy'{Colors.END} {Colors.GREEN}--limit 20{Colors.END}")
    print(f"  {Colors.DIM}$ {Colors.CYAN}{sys.argv[0]}{Colors.END} {Colors.GREEN}--batch{Colors.END} {Colors.GOLD}users.txt{Colors.END} {Colors.GREEN}--workers 10{Colors.END}\n")

def main():
    try:
        check_dependencies()
    except Exception as e:
        print(ColorUtils.warning(f"Dependency check failed: {e}"))
        print(ColorUtils.info("Continuing anyway..."))

    reset_environment()

    if len(sys.argv) < 2 or "--help" in sys.argv:
        show_help()
        sys.exit(0)

    use_tor = "--tor" in sys.argv
    no_cache = "--no-cache" in sys.argv
    proxy = None
    max_workers = 5

    for i, arg in enumerate(sys.argv):
        if arg == "--proxy" and i + 1 < len(sys.argv):
            proxy = sys.argv[i + 1]
        if arg == "--workers" and i + 1 < len(sys.argv):
            try:
                max_workers = max(1, int(sys.argv[i + 1]))
            except:
                pass

    limit = 10
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = max(1, int(sys.argv[i + 1]))
            except:
                pass

    if "--dashboard" in sys.argv:
        show_dashboard()
        return

    if "--search" in sys.argv:
        search_idx = sys.argv.index("--search")
        if search_idx + 1 < len(sys.argv):
            query = sys.argv[search_idx + 1]
            users = search_users(query, limit, use_cache=not no_cache, use_tor=use_tor, proxy=proxy)

            print(f"\n{Colors.GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗")
            print(f"{Colors.GREEN}║{Colors.GOLD}  {Icons.SEARCH}  {Colors.BOLD}Search Results{Colors.END}{Colors.GOLD}  {Icons.SEARCH}  {Colors.GREEN}                                                   ║")
            print(f"{Colors.GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
            print(f"{Colors.DIM}  Query: '{query}'  |  Found: {len(users)} users{Colors.END}\n")

            if users:
                for user in users[:limit]:
                    verified = f"{Colors.GREEN}{Icons.CHECK}{Colors.END}" if user.get('verified', False) else ""
                    print(f"  {Colors.CYAN}{Icons.DOUBLE_ARROW}{Colors.END} {Colors.PINK}@{user.get('username')}{Colors.END} {Colors.DIM}-{Colors.END} {user.get('name', 'N/A')} {Colors.DIM}({Colors.END}{Colors.GOLD}{user.get('numFollowers', 0):,}{Colors.END} {Colors.DIM}followers{Colors.END}{Colors.DIM}){Colors.END} {verified}")
            else:
                print(f"  {Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}No users found{Colors.END}")
            print()
        return

    if "--batch" in sys.argv:
        batch_idx = sys.argv.index("--batch")
        if batch_idx + 1 < len(sys.argv):
            filename = sys.argv[batch_idx + 1]
            if not os.path.exists(filename):
                print(ColorUtils.error(f"File not found: {filename}"))
                return
            batch_process(filename, use_cache=not no_cache, use_tor=use_tor, proxy=proxy, max_workers=max_workers)
        return

    if len(sys.argv) < 2:
        show_help()
        return

    username = sys.argv[1]

    if not validate_username(username):
        print(ColorUtils.error("Invalid username format"))
        return

    if "--monitor" in sys.argv:
        monitor_users(username, interval=3600, duration=86400, use_tor=use_tor, proxy=proxy)
        return

    if "--stories" in sys.argv:
        stories = extract_stories_data(username, limit, use_cache=not no_cache, use_tor=use_tor, proxy=proxy)

        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Colors.CYAN}║{Colors.GOLD}  {Icons.BOOK}  {Colors.BOLD}Stories by {Colors.END}{Colors.PINK}@{username}{Colors.GOLD}  {Icons.BOOK}  {Colors.CYAN}                                                 ║")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.DIM}  Found: {len(stories)} stories{Colors.END}\n")

        if stories:
            for story in stories[:limit]:
                print(f"  {Colors.CYAN}{Icons.DOUBLE_ARROW}{Colors.END} {Colors.WHITE}{story.get('title', 'N/A')}{Colors.END}")
                print(f"     {Colors.DIM}{Icons.DOT}{Colors.END} {Colors.DIM}Reads:{Colors.END} {Colors.GOLD}{story.get('readCount', 0):,}{Colors.END}  {Colors.DIM}Votes:{Colors.END} {Colors.PINK}{story.get('voteCount', 0):,}{Colors.END}  {Colors.DIM}Parts:{Colors.END} {Colors.CYAN}{story.get('numParts', 0)}{Colors.END}")
                print(f"     {Colors.DIM}{Icons.DOT}{Colors.END} {Colors.DIM}URL:{Colors.END} {Colors.BLUE}https://www.wattpad.com/story/{story.get('id')}{Colors.END}\n")
        else:
            print(f"  {Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}No stories found{Colors.END}\n")
        return

    if "--followers" in sys.argv:
        followers = extract_followers_data(username, limit, use_cache=not no_cache, use_tor=use_tor, proxy=proxy)

        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Colors.CYAN}║{Colors.GOLD}  {Icons.USERS}  {Colors.BOLD}Followers of {Colors.END}{Colors.PINK}@{username}{Colors.GOLD}  {Icons.USERS}  {Colors.CYAN}                                                ║")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.DIM}  Found: {len(followers)} followers{Colors.END}\n")

        if followers:
            for user in followers[:limit]:
                print(f"  {Colors.CYAN}{Icons.DOUBLE_ARROW}{Colors.END} {Colors.PINK}@{user.get('username')}{Colors.END} {Colors.DIM}-{Colors.END} {user.get('name', 'N/A')}")
        else:
            print(f"  {Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}No followers found{Colors.END}")
        print()
        return

    if "--following" in sys.argv:
        following = extract_following_data(username, limit, use_cache=not no_cache, use_tor=use_tor, proxy=proxy)

        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Colors.CYAN}║{Colors.GOLD}  {Icons.USERS}  {Colors.BOLD}Following of {Colors.END}{Colors.PINK}@{username}{Colors.GOLD}  {Icons.USERS}  {Colors.CYAN}                                                ║")
        print(f"{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.DIM}  Found: {len(following)} following{Colors.END}\n")

        if following:
            for user in following[:limit]:
                print(f"  {Colors.CYAN}{Icons.DOUBLE_ARROW}{Colors.END} {Colors.PINK}@{user.get('username')}{Colors.END} {Colors.DIM}-{Colors.END} {user.get('name', 'N/A')}")
        else:
            print(f"  {Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}No following found{Colors.END}")
        print()
        return

    profile = extract_profile_data(
        username,
        return_raw=False,
        use_cache=not no_cache,
        use_tor=use_tor,
        proxy=proxy
    )

    if profile:
        if "--json" in sys.argv:
            export_to_json(profile, username)
        elif "--csv" in sys.argv:
            export_to_csv(profile, username)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}{Icons.WARNING}{Colors.END} {Colors.DIM}Interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}{Icons.CROSS}{Colors.END} {Colors.BOLD}{Colors.RED}Error:{Colors.END} {e}")
        sys.exit(1)
