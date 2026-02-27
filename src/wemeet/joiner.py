import os
import platform
import subprocess
import time
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor
from typing import Optional

class WeMeetJoiner:
    """
    Handles joining WeMeet meetings.
    """
    def __init__(self, interactor: GUIInteractor):
        self.interactor = interactor
        self.system = platform.system()

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
            
            time.sleep(10)
            return self.verify_in_meeting()
        except Exception as e:
            logger.error(f"Failed to join via URL scheme: {e}")
            return False

    def join_via_gui(self, meeting_id: str) -> bool:
        """Fallback: Join using the WeMeet app UI."""
        logger.info("Falling back to GUI join.")
        
        # 0. Ensure app is open by clicking the icon (as requested by user)
        wemeet_icon = os.path.join("reference_img", "wemeeticon.png")
        if os.path.exists(wemeet_icon):
            logger.info(f"Clicking WeMeet icon: {wemeet_icon}")
            self.interactor.click_element(wemeet_icon, confidence=0.8)
            time.sleep(2) # Wait for app to come to front

        win = self.interactor.find_window(["WeMeet", "腾讯会议"])
        if not win:
            logger.error("WeMeet window not found.")
            return False

        try:
            # 1. Activate window
            self.interactor.activate_window(win)
            
            # 2. Click the 'Join' button (reference_img/wemeet_join.png)
            # This is the 'plus' or 'Join' button mentioned by the user
            join_btn = os.path.join("reference_img", "wemeet_join.png")
            if os.path.exists(join_btn):
                logger.info(f"Looking for join button image: {join_btn}")
                if self.interactor.click_element(join_btn, confidence=0.7):
                    time.sleep(1) # Wait for input field
                else:
                    logger.warning("Could not find join button image on screen. Trying direct type...")
            
            # 3. Type meeting ID
            self.interactor.type_safely(meeting_id)
            self.interactor.press_key('enter')
            
            time.sleep(5)
            return self.verify_in_meeting()
        except Exception as e:
            logger.error(f"Failed to join via GUI: {e}")
            return False

    def close_meeting(self) -> None:
        """Close the WeMeet window/meeting."""
        logger.info("Attempting to close WeMeet...")
        win = self.interactor.find_window(["WeMeet", "腾讯会议"])
        if win:
            self.interactor.activate_window(win)
            # Try Alt+Q (standard shortcut to leave/end)
            import pyautogui
            pyautogui.hotkey('alt', 'q')
            time.sleep(1)
            # Sometimes a confirmation dialog appears
            self.interactor.press_key('enter')
            logger.info("WeMeet close commands sent.")
        else:
            logger.warning("WeMeet window not found for closing.")

    def verify_in_meeting(self) -> bool:
        """Verify that we are in a meeting."""
        logger.info("Verifying meeting state...")
        win = self.interactor.find_window(["WeMeet", "腾讯会议"])
        if not win:
            return False

        try:
            box = win.box
            region = (int(box.left), int(box.top), int(box.width), int(box.height))
            text = self.interactor.ocr_region(region)
            
            meeting_keywords = ["mute", "unmute", "camera", "leave", "解除静音", "结束会议", "离开会议"]
            for kw in meeting_keywords:
                if kw.lower() in text.lower():
                    logger.info("Meeting join verified.")
                    return True
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            
        return False
