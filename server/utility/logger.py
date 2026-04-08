import logging
from colorama import Fore, Style, init

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "CORTEX_MAIN": Fore.CYAN,
        "CORTEX_VOICE": Fore.MAGENTA,
        "SENSORY": Fore.YELLOW,
        "CORTEX_MANAGER": Fore.GREEN,
        "CORTEX_MEMORY": Fore.BLUE,
        "TASK_QUEUE": Fore.RED,
        "DEFAULT": Fore.WHITE,
    }
    
    def format(self, record):
        component = record.name.upper()
        color = self.COLORS.get(component, Fore.WHITE)
        
        # Format the prefix: [COMPONENT] Message
        log_msg = f"{color}[{component}]{Style.RESET_ALL} {record.getMessage()}"
        return log_msg
 

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Avoid adding multiple handlers if called twice
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)
    
    return logger

__all__ = ["get_logger"]

