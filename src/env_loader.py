#!/usr/bin/env python3
"""
Environment variable loader for Bitcoin RPC configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_bitcoin_rpc_url():
    """Get Bitcoin RPC URL from environment variables."""
    user = os.getenv('BITCOIN_RPC_USER', 'bitcoinrpc')
    password = os.getenv('BITCOIN_RPC_PASSWORD', 'changeme')
    host = os.getenv('BITCOIN_RPC_HOST', '127.0.0.1')
    port = os.getenv('BITCOIN_RPC_PORT', '8332')

    return f"http://{user}:{password}@{host}:{port}/"

def should_use_torsocks():
    """Check if torsocks should be used."""
    return os.getenv('USE_TORSOCKS', 'false').lower() == 'true'

def get_ots_command_prefix():
    """Get the appropriate OTS command prefix."""
    if should_use_torsocks():
        return "torsocks ots"
    return "ots"
