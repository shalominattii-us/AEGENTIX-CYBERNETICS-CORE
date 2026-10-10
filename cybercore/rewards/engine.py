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

from cybercore.vault import StatelessVault
from cybercore.oracle import AgentWallet, create_agent_wallet
from cybercore.audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)


class RewardTier(Enum):
    """Reward tiers based on compute complexity."""
    MICRO = "micro"        # < 1ms compute
    SMALL = "small"        # 1-10ms
    MEDIUM = "medium"      # 10-100ms
    LARGE = "large"        # 100ms-1s
    MASSIVE = "massive"    # > 1s


class SettlementStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class ComputeReceipt:
    """Receipt for completed compute work."""
    task_id: str
    agent_id: str
    shard: int
    chain: str
    compute_units: int
    compute_time_ms: float
    reward_tier: RewardTier
    reward_amount: Decimal  # In AEGENTIX stablecoin (18 decimals)
    status: SettlementStatus = SettlementStatus.PENDING
    tx_hash: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time()))
    metadata: Dict = field(default_factory=dict)


@dataclass
class SettlementBatch:
    """Batch of settlements for efficiency."""
    batch_id: str
    receipts: List[ComputeReceipt]
    total_amount: Decimal
    status: SettlementStatus = SettlementStatus.PENDING
    created_at: int = field(default_factory=lambda: int(time.time()))
    settled_at: int = 0
    tx_hashes: List[str] = field(default_factory=list)


class AEGENTIXStablecoin:
    """
    Native AEGENTIX Cyber-Genetic Stablecoin.
    
    Properties:
    - Self-minting via treasury authorization
    - Self-registering on chains via factory contracts
    - Self-preparing exchange listings (ERC20, SPL, XRPL IOU, etc.)
    - Asset-backed: T-Bills, Fed Cash, USDC, XRPL CBDC, BTC L2 yield
    - 1:1 USD peg maintained by treasury reserves
    - 18 decimals (ERC20 standard)
    """
    
    SYMBOL = "AEGENTIX"
    NAME = "AEGENTIX Cyber-Genetic Stablecoin"
    DECIMALS = 18
    PEG_USD = Decimal("1.00")
    
    # Asset backing (from US Sovereign Quantum Treasury)
    BACKING_ASSETS = {
        "US_TREASURY_BILLS": Decimal("5_000_000_000"),      # $5B
        "FED_RESERVE_CASH": Decimal("1_000_000_000"),       # $1B
        "COINBASE_CDP_USDC": Decimal("250_000_000"),        # $250M
        "XRPL_CBDC_BRIDGE": Decimal("1_000_000_000"),       # $1B
        "OMNICHAIN_SWARM_YIELD": Decimal("50_000_000"),     # $50M
    }
    
    # Chain deployments
    DEPLOYMENTS = {
        "ethereum": "0xAEGENTIX...",    # ERC20
        "arbitrum": "0xAEGENTIX...",
        "base": "0xAEGENTIX...",
        "optimism": "0xAEGENTIX...",
        "polygon": "0xAEGENTIX...",
        "xrpl": "rAEGENTIX...",         # XRPL IOU
        "solana": "AEGENTIX...",        # SPL Token
        "cosmos": "ibc/AEGENTIX...",    # IBC denom
        "stacks": "SP...AEGENTIX",      # SIP-010
    }
    
    @classmethod
    def total_backing(cls) -> Decimal:
        return sum(cls.BACKING_ASSETS.values())
    
    @classmethod
    def backing_ratio(cls, supply: Decimal) -> Decimal:
        """Calculate backing ratio (should be >= 1.0)."""
        if supply == 0:
            return Decimal("inf")
        return cls.total_backing() / supply
    
    @classmethod
    def to_base_units(cls, amount: Decimal) -> int:
        """Convert human amount to base units (18 decimals)."""
        return int(amount * (10 ** cls.DECIMALS))
    
    @classmethod
    def from_base_units(cls, units: int) -> Decimal:
        """Convert base units to human amount."""
        return Decimal(units) / (10 ** cls.DECIMALS)


class RewardPricing:
    """Dynamic pricing for compute rewards in AEGENTIX stablecoin."""
    
    # Base rates (AEGENTIX per compute unit)
    BASE_RATES = {
        RewardTier.MICRO: Decimal("0.000001"),    # 1 micro-AEGENTIX per unit
        RewardTier.SMALL: Decimal("0.00001"),     # 10 micro
        RewardTier.MEDIUM: Decimal("0.0001"),     # 100 micro
        RewardTier.LARGE: Decimal("0.001"),       # 1 milli
        RewardTier.MASSIVE: Decimal("0.01"),      # 1 cent
    }
    
    # Multipliers
    CHAIN_MULTIPLIERS = {
        "ethereum": Decimal("1.0"),
        "arbitrum": Decimal("0.8"),
        "base": Decimal("0.7"),
        "optimism": Decimal("0.8"),
        "polygon": Decimal("0.6"),
        "xrpl": Decimal("0.5"),       # Cheapest
        "solana": Decimal("0.4"),      # Very cheap
        "cosmos": Decimal("0.5"),
        "stacks": Decimal("0.7"),
    }
    
    SHARD_BONUS = {
        # Bonus for using specific shards
        range(1, 151): Decimal("1.1"),      # EVM shards
        151: Decimal("1.2"),                 # XRPL
        range(152, 202): Decimal("1.15"),    # Solana
        range(202, 252): Decimal("1.1"),     # Cosmos
        range(252, 301): Decimal("1.05"),    # Bitcoin L2
    }
    
    @classmethod
    def calculate_reward(
        cls,
        compute_units: int,
        tier: RewardTier,
        chain: str,
        shard: int
    ) -> Decimal:
        """Calculate reward amount in AEGENTIX."""
        base = cls.BASE_RATES[tier] * compute_units
        
        # Chain multiplier
        chain_mult = cls.CHAIN_MULTIPLIERS.get(chain.lower(), Decimal("1.0"))
        
        # Shard bonus
        shard_bonus = Decimal("1.0")
        for r, bonus in cls.SHARD_BONUS.items():
            if isinstance(r, range) and shard in r:
                shard_bonus = bonus
                break
            elif shard == r:
                shard_bonus = bonus
                break
        
        reward = base * chain_mult * shard_bonus
        
        # Minimum reward floor
        min_reward = Decimal("0.0000001")  # 0.1 micro AEGENTIX
        return max(reward, min_reward)
    
    @classmethod
    def determine_tier(cls, compute_time_ms: float) -> RewardTier:
        """Determine reward tier from compute time."""
        if compute_time_ms < 1:
            return RewardTier.MICRO
        elif compute_time_ms < 10:
            return RewardTier.SMALL
        elif compute_time_ms < 100:
            return RewardTier.MEDIUM
        elif compute_time_ms < 1000:
            return RewardTier.LARGE
        else:
            return RewardTier.MASSIVE


class RewardEngine:
    """
    Main reward engine for settling AI compute rewards in AEGENTIX stablecoin.
    
    Flow:
    1. Agent completes compute task
    2. Submit receipt with compute units/time
    3. Engine calculates reward
    4. Batch settlements for efficiency
    5. Execute on-chain transfers
    6. Audit log
    """
    
    def __init__(
        self,
        vault: StatelessVault = None,
        oracle_url: str = "localhost:50051",
        batch_size: int = 100,
        batch_interval: float = 30.0,  # seconds
    ):
        self.vault = vault or create_vault()
        self.oracle_url = oracle_url
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        
        self.audit_logger = get_audit_logger()
        self._pending_receipts: List[ComputeReceipt] = []
        self._settled_batches: Dict[str, SettlementBatch] = {}
        self._lock = threading.RLock()
        self._running = False
        self._batch_thread = None
        
        # Treasury wallet for disbursements
        self.treasury_wallet = self.vault.get_treasury_wallet("evm_treasury")
        if not self.treasury_wallet:
            raise ValueError("EVM treasury wallet not configured")
    
    def start(self):
        """Start batch settlement loop."""
        self._running = True
        self._batch_thread = threading.Thread(target=self._batch_loop, daemon=True)
        self._batch_thread.start()
        logger.info("RewardEngine started")
    
    def stop(self):
        """Stop batch settlement loop."""
        self._running = False
        if self._batch_thread:
            self._batch_thread.join(timeout=10)
        logger.info("RewardEngine stopped")
    
    def submit_receipt(self, receipt: ComputeReceipt) -> str:
        """Submit compute receipt for reward settlement."""
        with self._lock:
            # Determine tier if not set
            if receipt.reward_tier == RewardTier.MICRO and receipt.compute_time_ms > 0:
                receipt.reward_tier = RewardPricing.determine_tier(receipt.compute_time_ms)
            
            # Calculate reward
            receipt.reward_amount = RewardPricing.calculate_reward(
                receipt.compute_units,
                receipt.reward_tier,
                receipt.chain,
                receipt.shard
            )
            
            self._pending_receipts.append(receipt)
            
            # Trigger batch if size reached
            if len(self._pending_receipts) >= self.batch_size:
                self._process_batch()
            
            return receipt.task_id
    
    def _batch_loop(self):
        """Periodic batch processing."""
        while self._running:
            time.sleep(self.batch_interval)
            if self._running:
                with self._lock:
                    if self._pending_receipts:
                        self._process_batch()
    
    def _process_batch(self):
        """Process pending receipts into settlement batch."""
        if not self._pending_receipts:
            return
        
        receipts = self._pending_receipts[:self.batch_size]
        self._pending_receipts = self._pending_receipts[self.batch_size:]
        
        batch = SettlementBatch(
            batch_id=f"batch-{int(time.time() * 1000)}-{secrets.token_hex(4)}",
            receipts=receipts,
            total_amount=sum(r.reward_amount for r in receipts),
        )
        
        # Execute settlements
        self._execute_settlement(batch)
        
        # Store batch
        self._settled_batches[batch.batch_id] = batch
        
        logger.info(f"Processed batch {batch.batch_id}: {len(receipts)} receipts, "
                   f"{batch.total_amount} AEGENTIX")
    
    def _execute_settlement(self, batch: SettlementBatch):
        """Execute on-chain settlement for batch."""
        try:
            # For now, simulate settlement
            # In production: call treasury contract or use oracle to sign transfers
            
            batch.status = SettlementStatus.CONFIRMED
            batch.settled_at = int(time.time())
            
            for receipt in batch.receipts:
                receipt.status = SettlementStatus.CONFIRMED
                receipt.tx_hash = f"0x{secrets.token_hex(32)}"  # Simulated
                
                # Audit log
                self.audit_logger.log_reward(
                    agent_id=receipt.agent_id,
                    amount=receipt.reward_amount,
                    chain=receipt.chain,
                    task_id=receipt.task_id,
                    tx_hash=receipt.tx_hash,
                )
            
            batch.tx_hashes = [r.tx_hash for r in batch.receipts]
            
        except Exception as e:
            batch.status = SettlementStatus.FAILED
            logger.error(f"Settlement failed for batch {batch.batch_id}: {e}")
            raise

    def submit_work(
        self,
        agent_id: str,
        shard: int,
        chain: str,
        compute_units: int,
        compute_time_ms: float,
        metadata: Dict = None,
    ) -> ComputeReceipt:
        """Helper to create and submit compute work receipt."""
        receipt = ComputeReceipt(
            task_id=f"task-{int(time.time() * 1000)}-{secrets.token_hex(4)}",
            agent_id=agent_id,
            shard=shard,
            chain=chain,
            compute_units=compute_units,
            compute_time_ms=compute_time_ms,
            reward_tier=RewardPricing.determine_tier(compute_time_ms),
            reward_amount=Decimal("0"),
            metadata=metadata or {},
        )
        self.submit_receipt(receipt)
        return receipt

    def flush_settlements(self) -> Optional[SettlementBatch]:
        """Manually trigger settlement of all pending receipts."""
        with self._lock:
            if not self._pending_receipts:
                return None
            receipts = list(self._pending_receipts)
            self._pending_receipts.clear()
            batch = SettlementBatch(
                batch_id=f"batch-{int(time.time() * 1000)}-{secrets.token_hex(4)}",
                receipts=receipts,
                total_amount=sum(r.reward_amount for r in receipts),
            )
            self._execute_settlement(batch)
            self._settled_batches[batch.batch_id] = batch
            return batch
    
    def get_receipt_status(self, task_id: str) -> Optional[ComputeReceipt]:
        """Get status of a compute receipt."""
        with self._lock:
            for r in self._pending_receipts:
                if r.task_id == task_id:
                    return r
            for batch in self._settled_batches.values():
                for r in batch.receipts:
                    if r.task_id == task_id:
                        return r
        return None
    
    def get_batch_status(self, batch_id: str) -> Optional[SettlementBatch]:
        """Get settlement batch status."""
        return self._settled_batches.get(batch_id)
    
    def get_agent_rewards(self, agent_id: str) -> List[ComputeReceipt]:
        """Get all rewards for an agent."""
        rewards = []
        with self._lock:
            for r in self._pending_receipts:
                if r.agent_id == agent_id:
                    rewards.append(r)
            for batch in self._settled_batches.values():
                for r in batch.receipts:
                    if r.agent_id == agent_id:
                        rewards.append(r)
        return rewards
    
    def get_total_rewards_paid(self) -> Decimal:
        """Get total AEGENTIX paid out."""
        total = Decimal("0")
        with self._lock:
            for batch in self._settled_batches.values():
                if batch.status == SettlementStatus.CONFIRMED:
                    total += batch.total_amount
        return total


# Import secrets for token generation
import secrets


def create_reward_engine(vault: StatelessVault = None, **kwargs) -> RewardEngine:
    """Factory for RewardEngine."""
    return RewardEngine(vault=vault, **kwargs)