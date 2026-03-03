import time
from src.wechat import WeChatController
from src.common.logger import agent_logger as logger

def test_wechat_messages_native():
    """
    Test to verify if we can extract content from the main WeChat message pane
    using WeChatController.
    """
    controller = WeChatController()
    logger.info("Testing get_messages from WeChatController...")
    
    messages = controller.get_messages(limit=20)
    
    if not messages:
        logger.error("Failed to retrieve messages or chat is empty.")
        return

    print("\n--- WeChat Main Chat History ---\n")
    
    for i, msg in enumerate(messages):
        print(f"[{i+1}] {msg}")
    
        # Check for meeting IDs
        ids = controller.extract_meeting_ids(msg)
        for meeting_id in ids:
            print(f"    >>> Meeting ID found: {meeting_id}")

    print("\n-----------------------------------\n")

if __name__ == "__main__":
    test_wechat_messages_native()
