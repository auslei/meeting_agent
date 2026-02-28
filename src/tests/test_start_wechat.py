import subprocess
import time
import os
from src.common.gui_interactor import GUIInteractor
from src.common.logger import agent_logger as logger

def test_start_wechat():
    """
    Test script to launch WeChat (Weixin) directly from its executable path.
    """
    wechat_path = r"C:\Program Files\Tencent\Weixin\Weixin.exe"
    
    if not os.path.exists(wechat_path):
        logger.error(f"WeChat executable not found at: {wechat_path}")
        return

    interactor = GUIInteractor()
    
    # 1. Check if it's already running
    win = interactor.find_window_native(r".*(WeChat|微信).*")
    if win:
        logger.info("WeChat is already running. Attempting to bring it to focus...")
        win.set_focus()
        return

    # 2. Launch the process
    logger.info(f"Launching WeChat from: {wechat_path}")
    try:
        subprocess.Popen([wechat_path], start_new_session=True)
        
        # 3. Wait for the window to appear
        logger.info("Waiting for WeChat window to appear (timeout 15s)...")
        max_retries = 15
        for i in range(max_retries):
            time.sleep(1)
            win = interactor.find_window_native(r".*(WeChat|微信).*")
            if win:
                logger.info("WeChat launched and window found successfully!")
                win.set_focus()
                return
            
        logger.error("WeChat launched but window did not appear in time.")
    except Exception as e:
        logger.error(f"Failed to launch WeChat: {e}")

if __name__ == "__main__":
    test_start_wechat()
