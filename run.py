import free
import sys


class Blank: pass
security_system = Blank()
security_system.device_id = free.get_device_id()

def main():
    
    try:
        
        if hasattr(free, 'banner'):
            free.banner()
        else:
            print("--- KP FREE VERSION ---")
            print(f"Device ID: {security_system.device_id}")
    except Exception as e:
        print(f"Banner error: {e}")

    
    print("[*] Starting main service...")
    try:
        
        session_id = free.get_session_id()
        
        if session_id == "ALREADY_ONLINE":
            print("[✓] Device is already online.")
            free.start_ping_monitor()
        elif session_id:
            print(f"[*] Session ID Found: {session_id}")
           
            voucher = input("[?] Enter Voucher Code: ").strip()
            free.login_voucher(session_id, voucher)
            free.start_ping_monitor()
        else:
            print("[!] Could not get valid session.")
            
    except Exception as e:
        print(f"[!] Error in main service: {e}")

if __name__ == "__main__":
    main()
