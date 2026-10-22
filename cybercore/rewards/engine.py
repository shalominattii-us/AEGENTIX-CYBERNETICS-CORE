"""
CyberCore Reward Engine - Native AEGENTIX Cyber-Genetic Stablecoin Settlements.

Rewards AI agents in the native AEGENTIX stablecoin (cyber-genetic, self-minting,
self-registering, exchange-listing ready) for ephemeral compute tasks.
"""

import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal

from cybercore.vault import StatelessVault, create_vault
from cybercore.oracle import AgentWallet, create_agent_wallet
from cybercore.audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)


class RewardTier(Enum):
    """Reward tiers based on compute complexity."""
    MICRO = "micro"        # < 1ms compute
    SMALL = "small"        #1-10ms
    MEDIUM = "medium"      # 10-100ms
    LARGE = "large"        # 100ms-1s
    MASSIVE = "massive"    # > 1s
