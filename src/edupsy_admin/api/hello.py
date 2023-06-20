""" Implement the hello command.

"""
from ..core.logger import logger


def main(id="World") -> str:
    """Execute the command.

    :param name: name to use in greeting
    """
    logger.debug(f"executing hello command with the return value 'Hello, {id}!'")
    return f"Hello, {id}!"
