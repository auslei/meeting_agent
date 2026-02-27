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

class GUIInteractor:
    """
    Robust base class for UI automation.
    """
    def __init__(self, pytesseract_path: Optional[str] = None):
        self._setup_tesseract(pytesseract_path)
        pyautogui.FAILSAFE = True

    def _setup_tesseract(self, path: Optional[str]) -> None:
        if path:
            pytesseract.pytesseract.tesseract_cmd = path
        elif platform.system() == "Windows":
            import os
            paths = [
                r'C:\Program Files\Tesseract-OCR	esseract.exe',
                r'C:\Users' + os.getlogin() + r'\AppData\Local\Tesseract-OCR	esseract.exe'
            ]
            for p in paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    return
            logger.warning("Tesseract not found in common Windows paths.")
        else:
            pytesseract.pytesseract.tesseract_cmd = 'tesseract'

    def find_window(self, title_keywords: List[str]) -> Optional[pwc.Window]:
        """Find a window by title keywords across platforms."""
        windows = pwc.getAllWindows()
        for win in windows:
            for kw in title_keywords:
                if kw.lower() in win.title.lower():
                    logger.info(f"Found window: {win.title}")
                    return win
        return None

    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Capture a specific region (x, y, w, h)."""
        screenshot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def ocr_region(self, region: Tuple[int, int, int, int]) -> str:
        """Perform OCR on a region."""
        img = self.capture_region(region)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, lang='chi_sim+eng').strip()
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
