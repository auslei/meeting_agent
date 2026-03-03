import time
from src.wechat import WeChatController
from src.common.logger import agent_logger as logger

def test_wechat_list_native():
    """
    Test to verify if we can extract all content from the WeChat message list
    using WeChatController.
    """
    controller = WeChatController()
    logger.info("Testing WeChatController logic for recent chats session list...")
    
    chats = controller.get_chat_list()
    
    if not chats:
        logger.error("Failed to retrieve chat list or list is empty.")
        return
        
    print("\n--- WeChat Recent Chats ---")
    for idx, chat in enumerate(chats):
        print(f"[{idx+1}] {chat}")
        
        # Check for meeting ID
        ids = controller.extract_meeting_ids(chat)
        for meeting_id in ids:
            print(f"    >>> Meeting ID detected: {meeting_id}")
            
    print("---------------------------\n")

if __name__ == "__main__":
    test_wechat_list_native()
