import pyautogui
from src.common.gui_interactor import GUIInteractor
from src.common.logger import agent_logger as logger
import cv2

def test_environment():
    try:
        size = pyautogui.size()
        logger.info(f"Screen size detected: {size}")
        
        interactor = GUIInteractor()
        
        # Test WeChat detection
        wechat_win = interactor.find_window(["WeChat", "微信"])
        if wechat_win:
            logger.info(f"SUCCESS: Found WeChat window at {wechat_win.box}")
            box = wechat_win.box
            region = (int(box.left), int(box.top), int(box.width), int(box.height))
            
            # Save diagnostic screenshot
            win_img = interactor.capture_region(region)
            cv2.imwrite("debug_wechat_window.png", win_img)
            logger.info("Saved diagnostic screenshot to debug_wechat_window.png")

            # Try OCR test
            text = interactor.ocr_region(region, debug_name="env_test")
            logger.info("WeChat OCR Full Result:")
            logger.info(text)
        else:
            logger.warning("FAILED: WeChat window not found. Is it minimized?")

        # Test WeMeet detection
        wemeet_win = interactor.find_window(["WeMeet", "腾讯会议"])
        if wemeet_win:
            logger.info(f"SUCCESS: Found WeMeet window at {wemeet_win.box}")
        else:
            logger.warning("FAILED: WeMeet window not found.")

    except Exception as e:
        logger.error(f"Environment test failed: {e}")

if __name__ == "__main__":
    test_environment()
