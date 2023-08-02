""" Application commands common to all interfaces.

"""
from .clients import Client, ClientsManager, collect_client_data_cli

__all__ = ("Client", "ClientsManager", "collect_client_data_cli")
