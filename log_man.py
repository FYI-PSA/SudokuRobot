import logging
from typing import Callable, Tuple

# import sys


def give_me_loggers() -> Tuple[Callable, Callable, Callable]:
    """Generates and gives you logging functions

    Returns:
        Tuple
        - Callable: An instant_info_logger function, takes only one thing, but anything, as an argument
        - Callable: An instant_error_logger function, same thing but it's red and cool
        - Callable: A stop_logging function, shuts down the logger
    """

    logging_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        format=logging_format,
        level=logging.INFO
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    # if for some reason it doesn't work with stdout
    # uncomment this:

    # formatter = logging.Formatter(logging_format)
    # stdout_handler = logging.StreamHandler(sys.stdout)
    # stdout_handler.setLevel(logging.INFO)
    # stdout_handler.setFormatter(formatter)
    # root_logger.addHandler(stdout_handler)

    def instant_info_logging(info) -> None:
        logging.info(info)
        logging.getLogger().handlers[0].flush()

    def instant_error_logging(info) -> None:
        logging.error(info)
        logging.getLogger().handlers[0].flush()

    def stop_logging() -> None:
        logging.shutdown()

    return (instant_info_logging, instant_error_logging, stop_logging)
