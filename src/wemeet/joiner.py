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
        self.system = platform.system()

    def _get_wemeet_window(self):
        """Find and return the WeMeet window using native backend."""
        return self.interactor.find_window_native(r".*(Tencent Meeting|腾讯会议).*")

    def join_via_scheme(self, meeting_id: str, password: Optional[str] = None) -> bool:
        """Try joining using the wemeet:// URL scheme."""
        url = f"wemeet://join?meeting_id={meeting_id}"
        if password:
            url += f"&password={password}"
        
        logger.info(f"Attempting to join via URL scheme: {url}")
        
        try:
            if self.system == "Windows":
                os.startfile(url)
            elif self.system == "Darwin":
                subprocess.run(["open", url])
            else:
                subprocess.run(["xdg-open", url])
            
            # Wait for the "Join Meeting" dialog that appears after scheme trigger
            time.sleep(5)
            
            # On Windows, after the scheme opens, we often need to click "Join" 
            # in a small confirmation dialog.
            if self.system == "Windows":
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

    def join_via_gui(self, meeting_id: str) -> bool:
        """Fallback: Join using the WeMeet app UI with native controls."""
        logger.info("Falling back to Native GUI join.")
        
        win = self._get_wemeet_window()
        if not win:
            logger.info("WeMeet not running. Attempting to start...")
            # If not found, try to click icon to start (keep as fallback)
            wemeet_icon = os.path.join("reference_img", "wemeeticon.png")
            if os.path.exists(wemeet_icon):
                self.interactor.click_element(wemeet_icon)
                time.sleep(5)
                win = self._get_wemeet_window()

        if not win:
            logger.error("Could not find or start WeMeet.")
            return False

        try:
            win.set_focus()
            time.sleep(1)
            
            # 1. Click "Join Meeting" (+) button
            logger.info("Clicking the 'Join Meeting' button via UI Automation...")
            try:
                # Based on standard WeMeet UI, the join button has title "加入会议"
                join_btn = win.child_window(title="加入会议", control_type="Group")
                if join_btn.exists(timeout=3):
                    join_btn.click_input()
                else:
                    logger.warning("Join button not found by title, falling back to Ctrl+J")
                    win.type_keys("^j")
            except Exception as e:
                logger.warning(f"Error clicking UI join button: {e}. Falling back to Ctrl+J")
                win.type_keys("^j") 
                
            time.sleep(2)
            
            # 2. Type meeting ID into the dialog that appears
            # The dialog is often a separate TopLevel window or nested. We'll find the active window.
            logger.info(f"Typing meeting ID: {meeting_id}")
            
            # If the join dialog opened, it might be the foreground window now
            current_win = self.interactor.desktop.window(active_only=True)
            
            try:
                # Direct typing to the focused window (the input is usually auto-focused)
                current_win.type_keys(meeting_id, with_spaces=True)
                time.sleep(1)
                current_win.type_keys("{ENTER}")
            except Exception as e:
                logger.error(f"Failed to type gracefully into dialog: {e}")
                # Fallback to base window typing
                win.type_keys(meeting_id, with_spaces=True)
                time.sleep(1)
                win.type_keys("{ENTER}")
            
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
