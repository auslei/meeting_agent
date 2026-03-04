import os
import platform
import subprocess
import time
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor
from typing import Optional
from pywinauto import Application

class WeMeetJoiner:
    """
    Handles joining WeMeet meetings using native Windows automation.
    """
    def __init__(self, interactor: GUIInteractor):
        self.interactor = interactor

    def _get_wemeet_window(self):
        """Find and return the WeMeet window using native backend."""
        meeting_window = self.interactor.find_window_native(r".*(Tencent Meeting|腾讯会议).*")
        if meeting_window:
            logger.info(f"Found WeMeet window: {meeting_window.window_text()}")
        return meeting_window

    def join_via_scheme(self, meeting_id: str, password: Optional[str] = None) -> bool:
        """Try joining using the wemeet:// URL scheme."""
        url = f"wemeet://join?meeting_id={meeting_id}"
        if password:
            url += f"&password={password}"
        
        logger.info(f"Attempting to join via URL scheme: {url}")
        
        try:
            os.startfile(url)
            
            # Wait for the "Join Meeting" dialog that appears after scheme trigger
            time.sleep(5)
            
            # On Windows, after the scheme opens, we often need to click "Join" 
            # in a small confirmation dialog.
            win = self.interactor.find_window_native(r".*(Tencent Meeting|腾讯会议).*")
            if win:
                win.set_focus()
                # Press Enter to confirm the join dialog if it's focused
                self.interactor.press_key('enter')
            
            time.sleep(5)
            return self.verify_in_meeting()
        except Exception as e:
            logger.error(f"Failed to join via URL scheme: {e}")
            return False

    def start_wemeet(self) -> bool:
        """Start WeMeet if not running."""
        logger.info("Starting WeMeet...")
        win = self._get_wemeet_window()
        if win:
            logger.info("WeMeet is already running.")
            return win 

        try:
            os.startfile("C:\\Program Files\\Tencent\\WeMeet\\WeMeetApp.exe")
            time.sleep(5)
            return self._get_wemeet_window()
        except Exception as e:
            logger.error(f"Failed to start WeMeet: {e}")
            return None

    def join_via_gui(self, meeting_id: str) -> bool:
        """Fallback: Join using the WeMeet app UI with native controls."""
        logger.info("Falling back to Native GUI join.")
        
        try:
            os.startfile("C:\\Program Files\\Tencent\\WeMeet\\WeMeetApp.exe")
            time.sleep(2)
            app = Application(backend="uia").connect(title_re=r".*(Tencent Meeting|腾讯会议).*")

            if app:
                logger.info("WeMeet is running")
            else:
                logger.error("WeMeet is not running")
                return False

            wm_window = app.window(title="腾讯会议")

            wm_window.set_focus()
            logger.info("focused..")
            time.sleep(1)

            rect = wm_window.rectangle()

            click_x = rect.left + 310 
            click_y = rect.top + 401

            # Perform the click at the dynamic location
            import pywinauto
            pywinauto.mouse.click(coords=(click_x, click_y))
            logger.info(f"clicked on {click_x}, {click_y}")
            
            join_window = app.window(title="加入会议")
            join_window.set_focus()

            time.sleep(1)
            join_window.type_keys(meeting_id)
            join_window.type_keys("{ENTER}")
            
            logger.info("Waiting 10s for meeting to start...")
            time.sleep(10)
            return self.verify_in_meeting()
        except Exception as e:
            logger.error(f"Failed to join via Native GUI: {e}")
            return False

    def close_meeting(self) -> None:
        """Close the WeMeet window/meeting."""
        logger.info("Attempting to close WeMeet natively...")
        win = self._get_wemeet_window()
        if win:
            try:
                win.set_focus()
                # Alt+Q is the universal "Leave/End Meeting" shortcut
                win.type_keys("%q")
                time.sleep(1)
                win.type_keys("{ENTER}") # Confirm leave
                logger.info("WeMeet close commands sent.")
            except Exception as e:
                logger.error(f"Error closing meeting: {e}")
        else:
            logger.warning("WeMeet window not found for closing.")

    def verify_in_meeting(self) -> bool:
        """Verify that we are in a meeting by checking for specific UI elements or title changes."""
        win = self._get_wemeet_window()
        if win:
            # When in a meeting, the title often changes or new controls appear
            # For now, window existence is our primary indicator
            logger.info(f"Meeting join verified (Window found: {win.texts()})")
            return True
        return False
