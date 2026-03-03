import time
from src.wechat import WeChatController
from src.common.logger import agent_logger as logger

def test_start_wechat():
    """
    Test script to launch WeChat using WeChatController.
    """
    controller = WeChatController()
    
    logger.info("Attempting to start WeChat...")
    success = controller.start_wechat()
    
    if success:
        logger.info("Test passed: WeChat is running and focused.")
    else:
        logger.error("Test failed: Could not start or focus WeChat.")

if __name__ == "__main__":
    test_start_wechat()
