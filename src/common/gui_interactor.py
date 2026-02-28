import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import time
from src.common.logger import agent_logger as logger
import pywinctl as pwc
import platform
from typing import Optional, List, Tuple
from pywinauto import Application, Desktop, WindowSpecification
from pywinauto.keyboard import send_keys

class GUIInteractor:
    """
    Robust base class for UI automation.
    Integrates pywinauto for stable Windows-native control interaction.
    """
    def __init__(self, pytesseract_path: Optional[str] = None):
        self._setup_tesseract(pytesseract_path)
        self.system = platform.system()
        pyautogui.FAILSAFE = True
        
        # Initialize pywinauto Desktop for UIA (Universal Image Automation) backend
        self.desktop = Desktop(backend="uia") if self.system == "Windows" else None

    def _setup_tesseract(self, path: Optional[str]) -> None:
        if path:
            pytesseract.pytesseract.tesseract_cmd = path
        elif platform.system() == "Windows":
            import os
            paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Users\\' + os.getlogin() + r'\AppData\Local\Tesseract-OCR\tesseract.exe'
            ]
            for p in paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    return
            logger.warning("Tesseract not found in common Windows paths.")
        else:
            pytesseract.pytesseract.tesseract_cmd = 'tesseract'

    def connect_app(self, title_re: str) -> Optional[Application]:
        """Connect to a running application by title regex."""
        if self.system != "Windows":
            return None
        try:
            app = Application(backend="uia").connect(title_re=title_re, timeout=5)
            return app
        except Exception as e:
            logger.debug(f"Could not connect to app with title regex '{title_re}': {e}")
            return None

    def find_window_native(self, title_re: str) -> Optional[WindowSpecification]:
        """Find a window using pywinauto, resolving ambiguity if multiple found."""
        if self.system != "Windows":
            return None
        try:
            # Get all matching windows
            all_wins = self.desktop.windows(title_re=title_re)
            if not all_wins:
                return None
            
            # If multiple, find the one that is likely the main window (visible and largest)
            if len(all_wins) > 1:
                logger.debug(f"Multiple windows found for '{title_re}'. Selecting the best match...")
                # Sort by area (width * height) descending
                best_win = max(all_wins, key=lambda w: w.rectangle().width() * w.rectangle().height())
                return self.desktop.window(handle=best_win.handle)
            
            return self.desktop.window(handle=all_wins[0].handle)
        except Exception as e:
            logger.debug(f"Native window search failed for '{title_re}': {e}")
        return None

    def click_button_native(self, window: WindowSpecification, auto_id: str = None, name: str = None) -> bool:
        """Click a button using pywinauto selectors."""
        try:
            if auto_id:
                btn = window.child_window(auto_id=auto_id, control_type="Button")
            elif name:
                btn = window.child_window(title=name, control_type="Button")
            else:
                return False
            
            if btn.exists(timeout=5):
                btn.click_input() # click_input is more reliable as it moves mouse
                logger.info(f"Clicked button: {auto_id or name}")
                return True
        except Exception as e:
            logger.error(f"Failed to click button '{auto_id or name}': {e}")
        return False

    def type_keys_native(self, window: WindowSpecification, text: str, auto_id: str = None) -> bool:
        """Type text into a control using pywinauto."""
        try:
            if auto_id:
                ctrl = window.child_window(auto_id=auto_id)
            else:
                # Fallback to current focus or standard typing
                window.type_keys(text, with_spaces=True)
                return True
            
            if ctrl.exists(timeout=5):
                ctrl.set_focus()
                ctrl.type_keys(text, with_spaces=True)
                logger.info(f"Typed '{text}' into {auto_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to type keys into '{auto_id}': {e}")
        return False

    def find_window_by_control(self, control_params: dict) -> Optional[WindowSpecification]:
        """
        Find a window by checking if it contains a specific child control.
        Useful when window titles are empty or dynamic.
        """
        if self.system != "Windows":
            return None
        
        logger.info(f"Searching for window containing control: {control_params}")
        for win in self.desktop.windows():
            try:
                # Check if the window has the child we're looking for
                child = win.child_window(**control_params)
                if child.exists(timeout=0.1):
                    logger.info(f"Found target window via control: '{win.window_text()}'")
                    return win
            except:
                continue
        return None

    def find_window(self, title_keywords: List[str]) -> Optional[pwc.Window]:
        """Find a window by title keywords across platforms."""
        windows = pwc.getAllWindows()
        for win in windows:
            for kw in title_keywords:
                if kw.lower() in win.title.lower():
                    logger.info(f"Found window: {win.title}")
                    return win
        return None

    def activate_window(self, win: pwc.Window) -> bool:
        """Bring window to foreground and focus it."""
        try:
            win.activate()
            # Some OSs require a small delay to focus
            time.sleep(0.5)
            logger.info(f"Activated window: {win.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate window {win.title}: {e}")
            return False

    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Capture a specific region (x, y, w, h)."""
        screenshot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def ocr_region(self, region: Tuple[int, int, int, int], debug_name: Optional[str] = None) -> str:
        """Perform OCR on a region with enhanced preprocessing."""
        img = self.capture_region(region)
        
        # Avoid double-upscaling on already large images (e.g. 5K screens)
        if img.shape[1] < 1000:
            img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Use simple thresholding as a fallback if adaptive is too noisy
        # For WeChat's light theme, this is often cleaner
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        if debug_name:
            debug_path = f"debug_{debug_name}.png"
            cv2.imwrite(debug_path, thresh)
            logger.debug(f"Saved OCR debug image to {debug_path}")

        text = pytesseract.image_to_string(thresh, lang='chi_sim+eng', config='--psm 6').strip()
        return text

    def click_element(self, image_path: str, confidence: float = 0.8, retries: int = 3, delay: float = 1.0) -> bool:
        """Robust click with retries."""
        for i in range(retries):
            try:
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    logger.info(f"Clicking {image_path} at {location}")
                    pyautogui.click(location)
                    return True
            except Exception as e:
                logger.error(f"Error during click: {e}")
            
            logger.warning(f"Retry {i+1}/{retries} for {image_path}...")
            time.sleep(delay)
        return False

    def wait_for_text(self, text: str, region: Optional[Tuple[int, int, int, int]] = None, timeout: int = 30) -> bool:
        """Wait for text to appear."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            detected = self.ocr_region(region) if region else pytesseract.image_to_string(pyautogui.screenshot())
            if text.lower() in detected.lower():
                return True
            time.sleep(1)
        return False

    def type_safely(self, text: str, interval: float = 0.05) -> None:
        """Type text safely."""
        logger.info(f"Typing: {text}")
        pyautogui.write(str(text), interval=interval)
        
    def press_key(self, key: str) -> None:
        logger.info(f"Pressing key: {key}")
        pyautogui.press(key)

    def search_wechat_chat(self, chat_name: str, timeout: int = 10) -> bool:
        """
        Search for a chat by its name in WeChat and click the result to open it.
        Works across systems by combining UIA and keyboard shortcuts.
        """
        if self.system != "Windows":
            logger.warning("search_wechat_chat is currently only optimized for Windows (UIA).")
            return False

        try:
            # 1. Find and Focus WeChat
            win = self.find_window_by_control({"auto_id": "main_tabbar", "control_type": "ToolBar"})
            if not win:
                win = self.find_window_native(r".*(WeChat|微信).*")
            
            if not win:
                logger.error("WeChat window not found. Cannot search.")
                return False

            win.set_focus()
            time.sleep(0.5)

            # 2. Trigger Search (Ctrl+F is a standard shortcut in WeChat for Windows)
            send_keys("^f")
            time.sleep(0.5)

            # 3. Locate the search box to ensure focus (fallback if Ctrl+F didn't focus)
            search_box = win.child_window(title="Search", control_type="Edit")
            if not search_box.exists(timeout=1):
                # Try broader search by control type 'Edit' (the top-left one)
                edits = win.descendants(control_type="Edit")
                if edits:
                    search_box = min(edits, key=lambda e: (e.rectangle().top, e.rectangle().left))
                else:
                    logger.error("Could not find search box in WeChat.")
                    return False
            
            # 4. Type the name and search
            logger.info(f"Searching for chat: '{chat_name}'")
            search_box.click_input()
            # Clear existing search (using Ctrl+A, Backspace)
            search_box.type_keys("^a{BACKSPACE}", with_spaces=True) 
            time.sleep(0.5)
            # Type the actual name
            search_box.type_keys(chat_name, with_spaces=True)
            time.sleep(1.5) # Wait for results

            # 5. Locate and click the result
            # We look for a ListItem that contains our target name
            # Often results are in a list with auto_id="search_result_list" or similar
            found = False
            
            # Strategy A: Look for exact name in all ListItems
            results = win.descendants(control_type="ListItem")
            for item in results:
                try:
                    name = item.window_text()
                    if chat_name.lower() in name.lower():
                        logger.info(f"Found search result: '{name}'. Clicking...")
                        item.click_input()
                        time.sleep(1)
                        found = True
                        break
                except:
                    continue
            
            if not found:
                # Strategy B: Fallback to Enter if we typed correctly
                logger.warning(f"Could not find explicit result for '{chat_name}', trying ENTER...")
                send_keys("{ENTER}")
                time.sleep(1)
                return True

            return found

        except Exception as e:
            logger.error(f"Error during search_wechat_chat: {e}")
            return False
