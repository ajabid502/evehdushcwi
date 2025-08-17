import streamlit as st
import requests
import time
import random
from stem import Signal
from stem.control import Controller
import stem.process
from fake_useragent import UserAgent
import pytz
from faker import Faker
from collections import OrderedDict
import socket
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import threading
import queue
import undetected_chromedriver as uc
from stem.connection import PasswordAuthFailed
from stem import SocketError
import json

# Configuration
WEBSITE_URL = st.secrets.get("WEBSITE_URL", "https://iphey.com")
TOR_PASSWORD = st.secrets.get("TOR_PASSWORD", "12345678")
TOR_PORT = int(st.secrets.get("TOR_PORT", 9050))
TOR_CONTROL_PORT = int(st.secrets.get("TOR_CONTROL_PORT", 9051))
PAGE_LOAD_TIME = (1, 3)
IP_API_URL = "http://ip-api.com/json/"  # Free IP geolocation API

# Search tasks configuration
SEARCH_TASKS = [
    ("Check browser fingerprints", "Check browser fingerprints", "https://iphey.com/")
]

# Enhanced device database with accurate platform fingerprints
DEVICES = {
    "Android": {
        "models": [
            {"name": "Samsung Galaxy S22", "code": "SM-S901B"},
            {"name": "Google Pixel 7", "code": "GP7"},
            {"name": "OnePlus 10 Pro", "code": "NE2213"},
            {"name": "Xiaomi Redmi Note 11", "code": "2201117TG"},
            {"name": "Samsung Galaxy S21 Ultra", "code": "SM-G998B"},
            {"name": "Google Pixel 6 Pro", "code": "GP6P"},
            {"name": "OnePlus 9 Pro", "code": "LE2123"},
            {"name": "Xiaomi Mi 11", "code": "M2011K2G"}
        ],
        "model_resolutions": {
            "SM-S901B": "1080x2400",
            "GP7": "1080x2400",
            "NE2213": "1440x3216",
            "2201117TG": "1080x2400",
            "SM-G998B": "1440x3200",
            "GP6P": "1440x3120",
            "LE2123": "1440x3216",
            "M2011K2G": "1440x3200"
        },
        "platform": "Linux armv8l",
        "user_agent_templates": [
            "Mozilla/5.0 (Linux; Android {version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android {version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36 EdgA/{edge_version}"
        ],
        "versions": ["11", "12", "13", "14", "15"],
        "chrome_versions": ["98.0.4758", "101.0.4951", "104.0.5112"],
        "edge_versions": ["98.0.1108", "101.0.1210"]
    },
    "iOS": {
        "models": [
            {"name": "iPhone 13", "code": "iPhone14,5"},
            {"name": "iPhone 13 Pro Max", "code": "iPhone14,3"},
            {"name": "iPhone 12", "code": "iPhone13,2"},
            {"name": "iPhone 12 Pro", "code": "iPhone13,3"},
            {"name": "iPhone SE (3rd gen)", "code": "iPhone14,6"},
            {"name": "iPhone 11", "code": "iPhone12,1"},
            {"name": "iPhone XR", "code": "iPhone11,8"},
            {"name": "iPad Air (4th gen)", "code": "iPad13,1"}
        ],
        "model_resolutions": {
            "iPhone14,5": "1170x2532",
            "iPhone14,3": "1284x2778",
            "iPhone13,2": "1170x2532",
            "iPhone13,3": "1170x2532",
            "iPhone14,6": "750x1334",
            "iPhone12,1": "828x1792",
            "iPhone11,8": "828x1792",
            "iPad13,1": "1640x2360"
        },
        "platform": "iPhone",
        "user_agent_templates": [
            "Mozilla/5.0 (iPhone; CPU iPhone OS {version} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS {version} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Mobile/15E148 Safari/604.1"
        ],
        "versions": ["14_5", "15_4", "16_0"],
        "safari_versions": ["14.1", "15.4", "16.0"]
    },
    "Windows": {
        "models": [
            {"name": "Desktop PC", "code": "Windows NT 10.0"},
            {"name": "Surface Pro", "code": "Touch; Tablet; Windows NT 10.0"}
        ],
        "resolutions": ["1920x1080", "1366x768", "1536x864", "2560x1440", "3440x1440", "3840x2160"],
        "platform": "Win32",
        "user_agent_templates": [
            "Mozilla/5.0 (Windows NT {version}; {architecture}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
            "Mozilla/5.0 (Windows NT {version}; {architecture}; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"
        ],
        "versions": ["10.0", "11.0"],
        "architectures": ["Win64; x64", "WOW64"],
        "chrome_versions": ["98.0.4758", "101.0.4951", "104.0.5112"],
        "firefox_versions": ["98.0", "101.0", "104.0"]
    },
    "macOS": {
        "models": [
            {"name": "MacBook Pro", "code": "Macintosh"},
            {"name": "iMac", "code": "Macintosh"}
        ],
        "resolutions": ["2560x1600", "2880x1800", "5120x2880", "2048x1536", "2560x1440", "3440x1440"],
        "platform": "MacIntel",
        "user_agent_templates": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X {version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X {version}; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X {version}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Safari/605.1.15"
        ],
        "versions": ["10_15_7", "11_6", "12_5"],
        "chrome_versions": ["98.0.4758", "101.0.4951", "104.0.5112"],
        "firefox_versions": ["98.0", "101.0", "104.0"],
        "safari_versions": ["14.1", "15.4", "16.0"]
    }
}

# Global variables with thread locks
session = None
tor_process = None
browser = None
message_queue = queue.Queue()
simulation_running = False
simulation_lock = threading.Lock()
browser_view_refresh = False

def get_ip_info(ip_address=None):
    """Get detailed IP information including timezone"""
    try:
        if ip_address:
            response = requests.get(f"{IP_API_URL}{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query", timeout=10)
        else:
            response = requests.get(f"{IP_API_URL}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data
        return None
    except Exception as e:
        message_queue.put(f"IP info lookup failed: {str(e)}")
        return None

def renew_tor_ip():
    """Force a new Tor IP with verification and return new IP info"""
    global session
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
                try:
                    controller.authenticate(password=TOR_PASSWORD)
                    old_ip_info = get_ip_info()
                    if not old_ip_info:
                        old_ip = session.get('https://api.ipify.org?format=json', timeout=10).json().get('ip')
                    else:
                        old_ip = old_ip_info.get('query')
                    
                    controller.signal(Signal.NEWNYM)
                    time.sleep(controller.get_newnym_wait())
                    
                    # Verify IP changed
                    new_ip_info = None
                    for _ in range(3):  # Try 3 times to get new IP info
                        new_ip_info = get_ip_info()
                        if new_ip_info:
                            new_ip = new_ip_info.get('query')
                            if new_ip != old_ip:
                                break
                        time.sleep(2)
                    
                    if not new_ip_info or new_ip == old_ip:
                        raise Exception("IP did not change after multiple attempts")
                    
                    message_queue.put(f"IP changed from {old_ip} ({old_ip_info.get('country', 'Unknown')}) to {new_ip} ({new_ip_info.get('country', 'Unknown')})")
                    return new_ip_info
                except PasswordAuthFailed:
                    message_queue.put("Error: Incorrect Tor controller password")
                    return None
        except SocketError:
            message_queue.put("Error: Could not connect to Tor controller")
            time.sleep(5)
        except Exception as e:
            message_queue.put(f"IP renewal failed (attempt {attempt+1}): {str(e)}")
            time.sleep(5)
    return None

def get_timezone_for_ip(ip_info):
    """Get timezone from IP info with fallback"""
    if ip_info and ip_info.get('timezone'):
        return ip_info['timezone']
    return "America/New_York"  # Default fallback

def get_random_device():
    """Generate random device profile with platform-specific properties"""
    platform = random.choice(list(DEVICES.keys()))
    device_info = DEVICES[platform]
    model = random.choice(device_info["models"])
    
    if platform in ["Android", "iOS"]:
        resolution = device_info["model_resolutions"][model["code"]]
    else:
        resolution = random.choice(device_info["resolutions"])
    
    width, height = resolution.split('x')
    
    return {
        "platform": platform,
        "os": platform,
        "model": model,
        "resolution": resolution,
        "width": width,
        "height": height,
        "platform_string": device_info["platform"],
        "touch_support": platform in ["Android", "iOS"]
    }

def generate_platform_user_agent(device):
    """Generate more varied platform-specific user agents"""
    platform = device["platform"]
    template_info = DEVICES[platform]
    template = random.choice(template_info["user_agent_templates"])
    
    def add_minor_version(version):
        if platform == "Android":
            return f"{version}.{random.randint(0,9)}"
        elif platform == "iOS":
            parts = version.split('_')
            return f"{parts[0]}_{parts[1]}_{random.randint(1,9)}"
        else:
            return version
    
    if platform == "Android":
        return template.format(
            version=add_minor_version(random.choice(template_info["versions"])),
            model=device["model"]["code"],
            chrome_version=f"{random.choice(template_info['chrome_versions'])}.{random.randint(0,99)}",
            edge_version=f"{random.choice(template_info['edge_versions'])}.{random.randint(0,99)}"
        )
    elif platform == "iOS":
        return template.format(
            version=add_minor_version(random.choice(template_info["versions"])),
            safari_version=f"{random.choice(template_info['safari_versions'])}.{random.randint(1,9)}"
        )
    elif platform == "Windows":
        return template.format(
            version=add_minor_version(random.choice(template_info["versions"])),
            architecture=random.choice(template_info["architectures"]),
            chrome_version=f"{random.choice(template_info['chrome_versions'])}.{random.randint(0,99)}",
            firefox_version=f"{random.choice(template_info['firefox_versions'])}.{random.randint(0,9)}"
        )
    elif platform == "macOS":
        return template.format(
            version=add_minor_version(random.choice(template_info["versions"])),
            chrome_version=f"{random.choice(template_info['chrome_versions'])}.{random.randint(0,99)}",
            firefox_version=f"{random.choice(template_info['firefox_versions'])}.{random.randint(0,9)}",
            safari_version=f"{random.choice(template_info['safari_versions'])}.{random.randint(1,9)}"
        )

def generate_fingerprint(device, ip_info=None):
    """Generate more realistic fingerprints with IP-based timezone"""
    fake = Faker()
    
    webgl_vendors = {
        "Android": "Qualcomm",
        "iOS": "Apple GPU",
        "Windows": "NVIDIA Corporation",
        "macOS": "Intel Inc."
    }
    
    webgl_renderers = {
        "Android": [
            "Adreno (TM) 650",
            "Adreno (TM) 630",
            "Mali-G78 MP20"
        ],
        "iOS": [
            "Apple GPU",
            "Apple A15 GPU"
        ],
        "Windows": [
            "GeForce RTX 3080/PCIe/SSE2",
            "GeForce RTX 3060/PCIe/SSE2",
            "Radeon RX 6700 XT"
        ],
        "macOS": [
            "Intel(R) Iris(TM) Plus Graphics OpenGL Engine",
            "Apple M1 Pro",
            "AMD Radeon Pro 5500M"
        ]
    }
    
    hw_concurrency = {
        "Windows": [4, 6, 8, 12, 16],
        "macOS": [4, 6, 8, 10],
        "Android": [4, 6, 8],
        "iOS": [4, 6]
    }
    
    device_memory = {
        "Windows": [4, 8, 16, 32],
        "macOS": [8, 16, 32],
        "Android": [4, 6, 8, 12],
        "iOS": [2, 4]
    }
    
    # Canvas fingerprint spoofing
    canvas_data = {
        "Android": {
            "font": "Arial",
            "text": "CanvasFingerprint",
            "color": "#"+fake.hex_color(),
            "size": "16px"
        },
        "iOS": {
            "font": "Helvetica",
            "text": "CanvasFingerprint",
            "color": "#"+fake.hex_color(),
            "size": "14px"
        },
        "Windows": {
            "font": "Arial",
            "text": "CanvasFingerprint",
            "color": "#"+fake.hex_color(),
            "size": "12px"
        },
        "macOS": {
            "font": "Helvetica",
            "text": "CanvasFingerprint",
            "color": "#"+fake.hex_color(),
            "size": "12px"
        }
    }
    
    # Use IP-based timezone if available
    timezone = get_timezone_for_ip(ip_info) if ip_info else "America/New_York"
    
    return {
        "canvas": {
            "data": canvas_data[device["platform"]],
            "hash": fake.sha1()
        },
        "webgl": {
            "vendor": webgl_vendors[device["platform"]],
            "renderer": random.choice(webgl_renderers[device["platform"]]),
            "hash": fake.sha1()
        },
        "audio": fake.sha1(),
        "visitorId": fake.uuid4(),
        "hardwareConcurrency": random.choice(hw_concurrency[device["platform"]]),
        "deviceMemory": random.choice(device_memory[device["platform"]]),
        "timezone": timezone,
        "language": random.choice(["en-US", "en-GB", "fr-FR", "de-DE", "es-ES"]),
        "doNotTrack": random.choice([True, False]),
        "webdriver": False,
        "platform": device["platform"],
        "ip_info": ip_info  # Store full IP info for reference
    }

def get_stealth_browser_options(device, fingerprint):
    """Create Chrome options with enhanced anti-detection measures"""
    chrome_options = Options()
    
    # Basic stealth options
    chrome_options.add_argument("--proxy-server=socks5://localhost:9050")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Window size based on device
    if device["platform"] in ["Windows", "macOS"]:
        chrome_options.add_argument(f"--window-size={device['width']},{device['height']}")
    else:  # Mobile
        chrome_options.add_argument("--window-size=360,640")
    
    # Advanced anti-detection measures
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=site-per-process")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Randomize user agent
    user_agent = generate_platform_user_agent(device)
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Disable automation flags
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Language settings
    chrome_options.add_argument(f"--lang={fingerprint['language'].split('-')[0]}")
    
    # For Streamlit display
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--mute-audio")
    
    return chrome_options

def override_navigator_properties(browser, fingerprint, device):
    """Override browser properties to avoid detection"""
    scripts = [
        # WebDriver flag
        "Object.defineProperty(navigator, 'webdriver', {get: () => false});",
        
        # Platform override
        f"Object.defineProperty(navigator, 'platform', {{get: () => '{device['platform_string']}'}});",
        
        # Hardware concurrency
        f"Object.defineProperty(navigator, 'hardwareConcurrency', {{value: {fingerprint['hardwareConcurrency']}}});",
        
        # Device memory
        f"Object.defineProperty(navigator, 'deviceMemory', {{value: {fingerprint['deviceMemory']}}});",
        
        # Languages
        f"Object.defineProperty(navigator, 'languages', {{get: () => ['{fingerprint['language']}', 'en-US', 'en']}});",
        
        # Plugins
        "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});",
        
        # MimeTypes
        "Object.defineProperty(navigator, 'mimeTypes', {get: () => [1, 2, 3, 4, 5]});",
        
        # Connection properties with randomization
        """
        Object.defineProperty(navigator, 'connection', {
            get: () => {
                const types = ['wifi', 'cellular', 'ethernet'];
                const effectiveTypes = ['4g', '5g'];
                const saveData = Math.random() > 0.8;
                
                return {
                    downlink: (Math.random() * 9 + 1).toFixed(1),
                    effectiveType: effectiveTypes[Math.floor(Math.random() * effectiveTypes.length)],
                    rtt: Math.floor(Math.random() * 150 + 50),
                    saveData: saveData,
                    type: types[Math.floor(Math.random() * types.length)]
                };
            }
        });
        """,
        
        # Canvas fingerprint override
        f"""
        HTMLCanvasElement.prototype.getContext = function(orig) {{
            return function(type, attributes) {{
                if (type === '2d') {{
                    const ctx = orig.call(this, type, attributes);
                    
                    const originalToDataURL = ctx.canvas.toDataURL;
                    ctx.canvas.toDataURL = function() {{
                        return 'data:image/png;base64,{fingerprint['canvas']['hash']}';
                    }};
                    
                    ctx.getImageData = function() {{
                        return new ImageData(1, 1);
                    }};
                    
                    return ctx;
                }}
                return orig.call(this, type, attributes);
            }};
        }}(HTMLCanvasElement.prototype.getContext);
        """,
        
        # WebGL fingerprint override
        f"""
        WebGLRenderingContext.prototype.getParameter = function(orig) {{
            return function(parameter) {{
                switch(parameter) {{
                    case this.VENDOR:
                        return '{fingerprint['webgl']['vendor']}';
                    case this.RENDERER:
                        return '{fingerprint['webgl']['renderer']}';
                    case this.UNMASKED_VENDOR_WEBGL:
                        return '{fingerprint['webgl']['vendor']}';
                    case this.UNMASKED_RENDERER_WEBGL:
                        return '{fingerprint['webgl']['renderer']}';
                    default:
                        return orig.call(this, parameter);
                }}
            }};
        }}(WebGLRenderingContext.prototype.getParameter);
        """,
        
        # AudioContext fingerprint override
        f"""
        AudioContext.prototype.createOscillator = function(orig) {{
            return function() {{
                const oscillator = orig.call(this);
                oscillator.frequency.value = {random.randint(440, 880)};
                return oscillator;
            }};
        }}(AudioContext.prototype.createOscillator);
        
        AudioContext.prototype.createAnalyser = function(orig) {{
            return function() {{
                const analyser = orig.call(this);
                analyser.fftSize = {random.choice([32, 64, 128, 256, 512])};
                return analyser;
            }};
        }}(AudioContext.prototype.createAnalyser);
        """
    ]
    
    for script in scripts:
        try:
            browser.execute_script(script)
        except Exception as e:
            message_queue.put(f"Failed to execute script: {str(e)}")

def get_random_headers(device, fingerprint):
    """Generate more natural headers with better ordering"""
    headers = OrderedDict([
        ('Host', urlparse(WEBSITE_URL).netloc),
        ('Connection', 'keep-alive'),
        ('Upgrade-Insecure-Requests', '1'),
        ('User-Agent', generate_platform_user_agent(device)),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        ('Sec-Fetch-Site', 'none'),
        ('Sec-Fetch-Mode', 'navigate'),
        ('Sec-Fetch-User', '?1'),
        ('Sec-Fetch-Dest', 'document'),
        ('Accept-Encoding', 'gzip, deflate, br'),
        ('Accept-Language', fingerprint["language"]),
        ('Cache-Control', 'max-age=0'),
        ('TE', 'trailers'),
        ('DNT', '1' if fingerprint["doNotTrack"] else '0'),
        ('Viewport-Width', device["width"]),
        ('Width', device["width"]),
        ('X-Timezone', fingerprint["timezone"]),
        ('X-Device-Model', device["model"]["name"]),
        ('X-Platform', device["platform"])
    ])
    
    if random.random() > 0.7:
        headers.pop('Upgrade-Insecure-Requests', None)
    if random.random() > 0.5:
        headers.pop('Sec-Fetch-User', None)
    
    if device["platform"] in ["Android", "iOS"]:
        headers.update({
            'X-Requested-With': 'com.android.chrome' if device["platform"] == "Android" else 'MobileSafari',
            'X-Mobile': 'true',
            'X-Device-Code': device["model"]["code"]
        })
    
    # Randomly add referrer
    if random.random() > 0.5:
        headers['Referer'] = random.choice([
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://www.facebook.com/',
            'https://twitter.com/'
        ])
    
    return headers

def simulate_real_navigation_timing():
    """Simulate realistic mouse movements and scrolling"""
    global browser
    if not browser:
        return
        
    try:
        scroll_pixels = random.randint(200, 800)
        scroll_direction = 1 if random.random() < 0.5 else -1
        browser.execute_script(f"window.scrollBy(0, {scroll_pixels * scroll_direction});")
        time.sleep(random.uniform(0.5, 2.0))
        
        if random.random() < 0.7:
            body = browser.find_element(By.TAG_NAME, 'body')
            actions = ActionChains(browser)
            actions.move_to_element(body)
            
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.1, 0.3))
            
            actions.perform()
            time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:
        message_queue.put(f"Navigation timing error: {str(e)}")

def simulate_platform_specific_behavior(device, fingerprint):
    """More realistic behavior patterns with randomization"""
    try:
        # Add random delays before any action
        random_delay(0.5, 2)
        
        # Desktop behavior patterns
        if device["platform"] in ["Windows", "macOS"] and browser:
            # Simulate mouse movements with more natural paths
            move_patterns = [
                [(100, 200), (150, 210), (180, 220)],  # Small precise movements
                [(100, 200), (300, 400), (200, 300)],  # Larger movements
                [(100, 200), (120, 190), (150, 180)],  # Upward movement
                [(100, 200), (80, 210), (70, 230)]     # Leftward movement
            ]
            
            pattern = random.choice(move_patterns)
            message_queue.put(f"Simulating mouse movement: {pattern}")
            
            actions = ActionChains(browser)
            for x, y in pattern:
                actions.move_by_offset(x, y).perform()
                random_delay(0.1, 0.3)  # Short pauses between movements
                # Add occasional tiny random movements
                if random.random() > 0.7:
                    actions.move_by_offset(random.randint(-5,5), random.randint(-5,5)).perform()
            
            # Random clicks (30% chance)
            if random.random() > 0.7:
                actions.click().perform()
                message_queue.put("Simulating random click")
                random_delay(0.5, 1.5)
        
        # Mobile behavior patterns
        elif device["platform"] in ["Android", "iOS"] and browser:
            # More varied touch simulation
            touch_events = random.randint(1, 5)
            message_queue.put(f"Simulating {touch_events} touch events")
            
            scroll_directions = [200, -200]  # Up and down
            for _ in range(touch_events):
                direction = random.choice(scroll_directions)
                browser.execute_script(f"window.scrollBy(0, {direction})")
                random_delay(0.2, 0.8)  # Variable delay between scrolls
                
                # Random zoom gestures (10% chance)
                if random.random() > 0.9:
                    browser.execute_script("document.body.style.zoom = '1.2'")
                    random_delay(0.3, 0.7)
                    browser.execute_script("document.body.style.zoom = '1.0'")
                    message_queue.put("Simulating zoom gesture")
        
        # Simulate reading patterns with varied scrolling
        scroll_events = random.randint(1, 5)
        scroll_amounts = [200, 300, 400, 500]
        
        for i in range(scroll_events):
            # Vary scroll speed and direction
            speed = random.uniform(0.5, 2.0)
            amount = random.choice(scroll_amounts)
            
            # Occasionally scroll up
            if i > 0 and random.random() > 0.7:
                amount = -amount
                
            message_queue.put(f"Simulating scroll event ({amount}px)")
            if browser:
                browser.execute_script(f"""
                    window.scrollBy({{
                        top: {amount},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """)
            
            # Variable delay with occasional longer pauses
            if random.random() > 0.8:
                pause = random.uniform(2, 5)
                message_queue.put(f"Pausing for {pause:.1f} seconds (reading)")
            else:
                pause = random.uniform(0.5, 1.5)
            time.sleep(pause)
            
        return True
    except Exception as e:
        message_queue.put(f"Behavior simulation error: {str(e)}")
        return False

def get_tor_session():
    """Create a new Tor session with randomized socket options"""
    session = requests.Session()
    session.proxies = {
        'http': f'socks5h://localhost:{TOR_PORT}',
        'https': f'socks5h://localhost:{TOR_PORT}'
    }
    
    # Randomize connection parameters
    socket_options = [
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
    ]
    
    # Randomly add additional socket options
    if random.random() > 0.5:
        socket_options.append((socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, random.randint(30, 120)))
    if random.random() > 0.5:
        socket_options.append((socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, random.randint(10, 30)))
    
    session.mount('http://', requests.adapters.HTTPAdapter(
        max_retries=random.randint(1, 3),
        socket_options=socket_options
    ))
    
    session.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=random.randint(1, 3),
        socket_options=socket_options
    ))
    
    # Randomize headers order for each session
    session.headers = OrderedDict([
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        ('Accept-Language', 'en-US,en;q=0.5'),
        ('Accept-Encoding', random.choice(['gzip, deflate, br', 'gzip, deflate'])),
        ('Connection', random.choice(['keep-alive', 'close'])),
        ('Upgrade-Insecure-Requests', '1'),
        ('Cache-Control', random.choice(['max-age=0', 'no-cache']))
    ])
    
    return session

def random_delay(min_seconds=None, max_seconds=None):
    """Random delay with more natural distribution"""
    if not hasattr(st.session_state, 'min_delay') or not hasattr(st.session_state, 'max_delay'):
        return time.sleep(1)
    
    min_val = min_seconds if min_seconds is not None else st.session_state.min_delay
    max_val = max_seconds if max_seconds is not None else st.session_state.max_delay
    
    # Use gamma distribution for more natural human-like delays
    delay = min(max(random.gammavariate(1.5, 1.5) * (max_val - min_val) / 3 + min_val, min_val), max_val)
    message_queue.put(f"Waiting {delay:.1f} seconds...")
    time.sleep(delay)

def simulate_page_load():
    """Simulate page load time with variations"""
    base_load = random.uniform(PAGE_LOAD_TIME[0], PAGE_LOAD_TIME[1])
    
    # Add random spikes for resource loading
    if random.random() > 0.3:
        spike_duration = random.uniform(0.1, 0.5)
        time.sleep(base_load + spike_duration)
    else:
        time.sleep(base_load)

def start_search_task(search_query, target_title, target_url, task_id):
    """Simulate a more natural search and visit with IP rotation"""
    global browser, browser_view_refresh, session
    
    try:
        # Force IP change before each task
        ip_info = renew_tor_ip()
        if not ip_info:
            message_queue.put("Failed to get new IP, aborting task")
            return False
        
        device = get_random_device()
        fingerprint = generate_fingerprint(device, ip_info)
        headers = get_random_headers(device, fingerprint)
        
        message_queue.put(f"\nStarting search task {task_id} from {ip_info.get('country', 'Unknown')}")
        message_queue.put(f"IP: {ip_info.get('query')}")
        message_queue.put(f"Location: {ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}")
        message_queue.put(f"Timezone: {fingerprint['timezone']}")
        message_queue.put(f"Search query: '{search_query}'")
        
        # Update browser view
        if browser:
            browser_view_refresh = True
        
        # Simulate typing with variable speed
        message_queue.put(f"Typing search query: '{search_query}'")
        typing_delay = random.gammavariate(1.5, 0.3)  # Human-like typing speed
        time.sleep(typing_delay * len(search_query) / 10)
        
        # Simulate Google search
        message_queue.put("Performing search...")
        random_delay(1, 3)
        
        # Simulate scanning results
        message_queue.put("Scanning results...")
        scan_time = random.gammavariate(2, 0.5)
        time.sleep(min(scan_time, 5))
        
        # Simulate clicking on result
        message_queue.put(f"Clicking on: '{target_title}'")
        random_delay(0.5, 1.5)
        
        # Visit target URL in browser
        if browser:
            try:
                browser.get(target_url)
                simulate_page_load()
                
                # Update browser view
                browser_view_refresh = True
            except Exception as e:
                message_queue.put(f"Browser navigation error: {str(e)}")
        
        # Randomly decide to leave quickly or stay
        if random.random() > 0.3:
            try:
                response = session.get(target_url, headers=headers, timeout=30)
                message_queue.put(f"Status: {response.status_code}")
                
                # Simulate reading time
                read_time = random.gammavariate(3, 1)
                message_queue.put(f"Reading content for {read_time:.1f} seconds")
                time.sleep(min(read_time, 30))
            except Exception as e:
                message_queue.put(f"Request failed: {str(e)}")
        else:
            message_queue.put("Leaving quickly (bounce)")
            time.sleep(random.uniform(3, 8))
        
        return True
        
    except Exception as e:
        message_queue.put(f"Error during search task: {str(e)}")
        return False

def simulate_visit(visit_num):
    """Simulate a visit with forced IP change and timezone sync"""
    global browser, browser_view_refresh, session
    
    try:
        # Force IP change before each visit
        ip_info = renew_tor_ip()
        if not ip_info:
            message_queue.put("Failed to get new IP, aborting visit")
            return False
        
        device = get_random_device()
        fingerprint = generate_fingerprint(device, ip_info)
        headers = get_random_headers(device, fingerprint)
        
        message_queue.put(f"\nVisit #{visit_num + 1} from {ip_info.get('country', 'Unknown')}")
        message_queue.put(f"IP: {ip_info.get('query')}")
        message_queue.put(f"Location: {ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}")
        message_queue.put(f"Timezone: {fingerprint['timezone']}")
        message_queue.put(f"ISP: {ip_info.get('isp', 'Unknown')}")
        message_queue.put(f"Device: {device['model']['name']} ({device['model']['code']})")
        message_queue.put(f"WebGL: {fingerprint['webgl']['vendor']}/{fingerprint['webgl']['renderer']}")
        message_queue.put(f"Hardware: {fingerprint['hardwareConcurrency']} cores, {fingerprint['deviceMemory']}GB RAM")
        
        if not simulate_platform_specific_behavior(device, fingerprint):
            return False
        
        message_queue.put("Loading page...")
        simulate_page_load()
        
        # Visit URL in browser
        if browser:
            try:
                browser.get(WEBSITE_URL)
                browser_view_refresh = True
            except Exception as e:
                message_queue.put(f"Browser navigation error: {str(e)}")
        
        # Randomly decide to actually visit or abort
        if random.random() > 0.1:  # 10% chance to abort
            try:
                response = session.get(WEBSITE_URL, headers=headers, timeout=30)
                message_queue.put(f"Status: {response.status_code}")
                
                # Check IP
                try:
                    ip_check = session.get('https://api.ipify.org?format=json', timeout=10)
                    message_queue.put(f"Current IP: {ip_check.json()['ip']}")
                except:
                    message_queue.put("IP check failed (intentional for realism)")
                
                # Random navigation patterns
                if random.random() > 0.6:
                    message_queue.put("Navigating to second page")
                    random_delay(2, 5)
                    if browser:
                        browser.get(f"{WEBSITE_URL}/page2")
                        browser_view_refresh = True
                    session.get(f"{WEBSITE_URL}/page2", headers=headers, timeout=20)
                
                return True
            except Exception as e:
                message_queue.put(f"Request failed: {str(e)}")
                return False
        else:
            message_queue.put("Aborting visit (simulating user change of mind)")
            return False
        
    except Exception as e:
        message_queue.put(f"Error during visit: {str(e)}")
        return False

def run_simulation():
    global session, tor_process, browser, simulation_running, browser_view_refresh
    
    with simulation_lock:
        simulation_running = True
        message_queue.put("Starting advanced traffic simulation with anti-detection measures...")
        message_queue.put(f"Target website: {WEBSITE_URL}")
        
        try:
            # Start Tor
            message_queue.put("Starting Tor process...")
            try:
                tor_process = stem.process.launch_tor_with_config(
                    config={
                        'SocksPort': str(TOR_PORT),
                        'ControlPort': str(TOR_CONTROL_PORT),
                        'HashedControlPassword': '16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C',
                    },
                    take_ownership=True,
                )
            except Exception as e:
                message_queue.put(f"Tor may already be running or there was an error starting it: {str(e)}")
                tor_process = None
            
            # Start browser with enhanced stealth
            try:
                # Get initial IP info
                session = get_tor_session()
                ip_info = get_ip_info()
                
                device = get_random_device()
                fingerprint = generate_fingerprint(device, ip_info)
                
                # Use undetected-chromedriver for better stealth
                chrome_options = get_stealth_browser_options(device, fingerprint)
                
                # Additional experimental options
                chrome_options.add_argument("--disable-3d-apis")
                chrome_options.add_argument("--disable-webgl")
                chrome_options.add_argument("--disable-canvas-aa")
                chrome_options.add_argument("--disable-canvas-texture-sharing")
                
                # Disable automation detection
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                
                # Start browser
                browser = uc.Chrome(options=chrome_options)
                
                # Override navigator properties
                override_navigator_properties(browser, fingerprint, device)
                
                # Set viewport size
                browser.set_window_size(int(device['width']), int(device['height']))
                
                message_queue.put("Browser started with enhanced anti-detection measures")
                browser_view_refresh = True
            except Exception as e:
                message_queue.put(f"Could not start browser: {str(e)}")
                browser = None
            
            successful_visits = 0
            for i in range(st.session_state.num_visits):
                if not simulation_running:
                    break
                    
                message_queue.put(f"\nStarting visit {i+1} of {st.session_state.num_visits}")
                
                # Alternate between direct visits and search tasks
                if random.choice([True, False]):
                    search_query, target_title, target_url = random.choice(SEARCH_TASKS)
                    if start_search_task(search_query, target_title, target_url, i+1):
                        successful_visits += 1
                else:
                    if simulate_visit(i):
                        successful_visits += 1
                
                if i < st.session_state.num_visits - 1 and simulation_running:
                    random_delay()
            
            message_queue.put(f"\nSimulation complete. {successful_visits}/{st.session_state.num_visits} successful visits.")
            
        finally:
            # Cleanup
            if browser:
                try:
                    browser.quit()
                except:
                    pass
            if tor_process:
                try:
                    tor_process.kill()
                except:
                    pass
            
            simulation_running = False
            st.session_state.simulation_complete = True
            st.rerun()

def stop_simulation():
    global simulation_running
    with simulation_lock:
        simulation_running = False
        message_queue.put("\nSimulation stopped by user")

def display_browser_view():
    """Display the browser view with current status"""
    global browser
    if browser and hasattr(browser, 'service') and browser.service.process:
        try:
            # Take screenshot and convert to bytes
            screenshot = browser.get_screenshot_as_png()
            st.image(screenshot, caption="Current Browser View", use_column_width=True)
        except Exception as e:
            st.warning(f"Could not get browser screenshot: {str(e)}")

def main():
    global browser_view_refresh
    
    st.set_page_config(page_title="Advanced Traffic Simulator", layout="wide")
    st.title("Advanced Traffic Simulator with Tor and Anti-Detection")
    
    # Initialize session state
    if 'num_visits' not in st.session_state:
        st.session_state.num_visits = 10
    if 'min_delay' not in st.session_state:
        st.session_state.min_delay = 5
    if 'max_delay' not in st.session_state:
        st.session_state.max_delay = 15
    if 'simulation_complete' not in st.session_state:
        st.session_state.simulation_complete = False
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'log_content' not in st.session_state:
        st.session_state.log_content = ""
    
    # Sidebar controls
    with st.sidebar:
        st.header("Simulation Settings")
        st.session_state.num_visits = st.slider("Number of visits", 1, 50, st.session_state.num_visits)
        st.session_state.min_delay = st.slider("Minimum delay between actions (seconds)", 1, 30, st.session_state.min_delay)
        st.session_state.max_delay = st.slider("Maximum delay between actions (seconds)", 1, 60, st.session_state.max_delay)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Simulation", disabled=st.session_state.simulation_running):
                st.session_state.simulation_complete = False
                st.session_state.simulation_running = True
                threading.Thread(target=run_simulation).start()
        with col2:
            st.button("Stop Simulation", on_click=stop_simulation, disabled=not st.session_state.simulation_running)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("Browser View")
        browser_placeholder = st.empty()
    
    with col2:
        st.header("Simulation Log")
        log_placeholder = st.empty()
    
    # Update UI elements
    while True:
        # Check if simulation is still running
        if not simulation_running and st.session_state.simulation_complete:
            st.session_state.simulation_running = False
            st.rerun()
            break
        
        # Update log
        new_messages = []
        while not message_queue.empty():
            new_messages.append(message_queue.get())
        
        if new_messages:
            st.session_state.log_content += "\n".join(new_messages) + "\n"
            # Limit to last 10k chars to prevent memory issues
            log_placeholder.code(st.session_state.log_content[-10000:])
        
        # Update browser screenshot
        if browser_view_refresh and browser and simulation_running:
            try:
                with browser_placeholder.container():
                    display_browser_view()
                browser_view_refresh = False
            except Exception as e:
                message_queue.put(f"Screenshot error: {str(e)}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()