import time
from src.common.logger import agent_logger as logger
from typing import Optional, List
from pywinauto import Application, Desktop, WindowSpecification
from pywinauto.keyboard import send_keys

class GUIInteractor:
    """
    Robust base class for UI automation.
    Integrates pywinauto for stable Windows-native control interaction.
    """
    def __init__(self):
        # Initialize pywinauto Desktop for UIA (Universal Image Automation) backend
        self.desktop = Desktop(backend="uia")

    def connect_app(self, title_re: str) -> Optional[Application]:
        """Connect to a running application by title regex."""
        try:
            app = Application(backend="uia").connect(title_re=title_re, timeout=5)
            return app
        except Exception as e:
            logger.debug(f"Could not connect to app with title regex '{title_re}': {e}")
            return None

    def find_window_native(self, title_re: str) -> Optional[WindowSpecification]:
        """Find a window using pywinauto, resolving ambiguity if multiple found."""
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

    def press_key(self, key: str) -> None:
        logger.info(f"Typing key: {{{key}}}")
        send_keys(f"{{{key}}}")
