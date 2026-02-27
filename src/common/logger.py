from loguru import logger
import sys
import os

def setup_logger(log_file: str = "cu_agent.log", level: str = "DEBUG"):
    """
    Configure loguru for the project.
    """
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(sys.stderr, level=level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # File handler
    logger.add(log_file, rotation="10 MB", level=level, backtrace=True, diagnose=True)
    
    return logger

# Default logger instance
agent_logger = setup_logger()
