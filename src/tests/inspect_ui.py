from pywinauto import Desktop
import sys

def inspect_windows():
    """
    Improved utility to print UI control identifiers.
    Uses WindowSpecification for better reliability.
    """
    print("\n--- Scanning for WeChat and WeMeet windows ---\n")
    
    desktop = Desktop(backend="uia")
    targets = ["WeChat", "微信", "WeMeet", "腾讯会议", "Meeting"]
    
    found_any = False
    
    # Get all window handles first to avoid iteration issues
    for win in desktop.windows():
        title = win.window_text()
        if any(kw in title for kw in targets):
            print(f"\n[*] Found Target Window: '{title}' (Handle: {win.handle})")
            found_any = True
            try:
                # Connect specifically to this window handle
                # This returns a WindowSpecification which has print_control_identifiers
                spec = desktop.window(handle=win.handle)
                spec.print_control_identifiers()
                print("-" * 60)
            except Exception as e:
                print(f"[!] Could not inspect '{title}': {e}")
                # Fallback: try simple dump if available
                try:
                    print("[*] Attempting fallback dump...")
                    print(win.get_properties())
                except:
                    pass

    if not found_any:
        print("[!] No target windows found. Please ensure WeChat or WeMeet are open and visible.")

if __name__ == "__main__":
    inspect_windows()

with UIPath(u"腾讯会议||Windo"):
	wrapper = find(u"")
	wrapper.draw_outline()

with UIPath(u"加入会议||Window"):
	wrapper = find(u"DialogWidget||Group->join_meeting_dialog||Group->加入会议||Button->加入会议||Text")
	wrapper.draw_outline()
