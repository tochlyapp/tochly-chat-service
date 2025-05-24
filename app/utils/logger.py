import logging

def get_logger(name: str = 'app'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Avoid adding multiple handlers if re-imported
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
 