""" Implement the hello command.

"""
from ..core.logger import logger


def main(idcode="World") -> str:
    """Execute the command.

    :param name: name to use in greeting
    """
    logger.debug(f"executing hello command with the return value 'Hello, {idcode}!'")
    return f"Hello, {idcode}!"
