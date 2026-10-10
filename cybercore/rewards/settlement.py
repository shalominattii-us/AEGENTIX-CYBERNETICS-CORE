"""
Reward Settlement Module - On-chain execution for AEGENTIX stablecoin transfers.
Supports EVM (ERC20), XRPL (IOU), Solana (SPL), Cosmos (IBC), Bitcoin L2.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

from cybercore.rewards.engine import RewardEngine, ComputeReceipt, SettlementBatch, SettlementStatus
from cybercore.vault import StatelessVault
from cybercore.derivation import get_chain_registry, ChainFamily

logger = logging.getLogger(__name__)


@dataclass
class SettlementConfig:
    """Configuration for settlement on a specific chain."""
    chain: str
    treasury_address: str
    stablecoin_contract: str
    gas_limit: int = 100000
    gas_price_gwei: int = 20
    confirmations: int = 1
    timeout_seconds: int = 120


# Settlement configurations per chain
SETTLEMENT_CONFIGS = {
    "ethereum": SettlementConfig(
        chain="ethereum",
        treasury_address="0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        stablecoin_contract="0xAEGENTIX...",  # AEGENTIX ERC20
        gas_limit=150000,
        gas_price_gwei=20,
    ),
    "arbitrum": SettlementConfig(
        chain="arbitrum",
        treasury_address="0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        stablecoin_contract="0xAEGENTIX...",
        gas_limit=150000,
        gas_price_gwei=1,
    ),
    "base": SettlementConfig(
        chain="base",
        treasury_address="0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        stablecoin_contract="0xAEGENTIX...",
        gas_limit=150000,
        gas_price_gwei=1,
    ),
    "optimism": SettlementConfig(
        chain="optimism",
        treasury_address="0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        stablecoin_contract="0xAEGENTIX...",
        gas_limit=150000,
        gas_price_gwei=1,
    ),
    "polygon": SettlementConfig(
        chain="polygon",
        treasury_address="0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        stablecoin_contract="0xAEGENTIX...",
        gas_limit=200000,
        gas_price_gwei=30,
    ),
    "xrpl": SettlementConfig(
        chain="xrpl",
        treasury_address="rZamanXRPLMainnetVaultAddr9948271",
        stablecoin_contract="AEGENTIX",  # XRPL IOU currency code
        gas_limit=0,  # Not applicable
        gas_price_gwei=0,
    ),
    "solana": SettlementConfig(
        chain="solana",
        treasury_address="SolanaMinimalTreasuryVault111111111111111111",
        stablecoin_contract="AEGENTIX...",  # SPL Token mint
        gas_limit=0,
        gas_price_gwei=0,
    ),
    "cosmos": SettlementConfig(
        chain="cosmos",
        treasury_address="cosmos1aegentixminimaltreasuryvault99999",
        stablecoin_contract="ibc/AEGENTIX...",  # IBC denom
        gas_limit=200000,
        gas_price_gwei=0,
    ),
    "stacks": SettlementConfig(
        chain="stacks",
        treasury_address="bc1qaegentixminimalnodebtc2026vault999",
        stablecoin_contract="SP...AEGENTIX",  # SIP-010
        gas_limit=0,
        gas_price_gwei=0,
    ),
}


class SettlementExecutor:
    """Executes on-chain settlements for reward batches."""
    
    def __init__(self, vault: StatelessVault):
        self.vault = vault
        self.registry = get_chain_registry()
    
    def settle_batch(self, batch: SettlementBatch) -> List[str]:
        """
        Execute settlement for a batch.
        Returns list of transaction hashes.
        """
        tx_hashes = []
        
        # Group receipts by chain for batch transactions
        by_chain: Dict[str, List[ComputeReceipt]] = {}
        for receipt in batch.receipts:
            if receipt.chain not in by_chain:
                by_chain[receipt.chain] = []
            by_chain[receipt.chain].append(receipt)
        
        for chain, receipts in by_chain.items():
            try:
                chain_hashes = self._settle_chain(chain, receipts)
                tx_hashes.extend(chain_hashes)
            except Exception as e:
                logger.error(f"Failed to settle {chain}: {e}")
                # Mark failed receipts
                for r in receipts:
                    r.status = SettlementStatus.FAILED
        
        return tx_hashes
    
    def _settle_chain(self, chain: str, receipts: List[ComputeReceipt]) -> List[str]:
        """Settle rewards on a specific chain."""
        config = SETTLEMENT_CONFIGS.get(chain)
        if not config:
            raise ValueError(f"No settlement config for chain: {chain}")
        
        chain_config = self.registry.get(chain)
        if not chain_config:
            raise ValueError(f"Unknown chain: {chain}")
        
        tx_hashes = []
        
        if chain_config.family == ChainFamily.EVM:
            tx_hashes = self._settle_evm(config, receipts)
        elif chain_config.family == ChainFamily.XRPL:
            tx_hashes = self._settle_xrpl(config, receipts)
        elif chain_config.family == ChainFamily.SOLANA:
            tx_hashes = self._settle_solana(config, receipts)
        elif chain_config.family == ChainFamily.COSMOS:
            tx_hashes = self._settle_cosmos(config, receipts)
        elif chain_config.family == ChainFamily.BITCOIN_L2:
            tx_hashes = self._settle_bitcoin_l2(config, receipts)
        else:
            raise ValueError(f"Unsupported chain family: {chain_config.family}")
        
        return tx_hashes
    
    def _settle_evm(self, config: SettlementConfig, receipts: List[ComputeReceipt]) -> List[str]:
        """Execute ERC20 transfers on EVM chain."""
        # In production: use web3.py to call ERC20.transfer or ERC20.transferFrom
        # For now, simulate
        tx_hashes = []
        
        # Could batch multiple transfers in one multicall
        for receipt in receipts:
            # Simulate transaction
            amount_wei = AEGENTIXStablecoin.to_base_units(receipt.reward_amount)
            
            # Build transaction
            tx_data = {
                "to": config.stablecoin_contract,
                "data": self._encode_erc20_transfer(receipt.address, amount_wei),
                "gas": config.gas_limit,
                "gasPrice": config.gas_price_gwei * 10**9,
            }
            
            # Sign via oracle
            # signature = self.vault.sign(...)
            
            # Simulated tx hash
            tx_hash = f"0x{secrets.token_hex(32)}"
            tx_hashes.append(tx_hash)
            
            logger.info(f"Simulated ERC20 transfer: {receipt.reward_amount} AEGENTIX "
                       f"to {receipt.address} on {config.chain}")
        
        return tx_hashes
    
    def _encode_erc20_transfer(self, to: str, amount: int) -> bytes:
        """Encode ERC20 transfer calldata."""
        # transfer(address,uint256) selector: 0xa9059cbb
        selector = bytes.fromhex("a9059cbb")
        # Pad address to 32 bytes
        addr_bytes = bytes.fromhex(to[2:]).rjust(32, b'\x00')
        # Pad amount to 32 bytes
        amount_bytes = amount.to_bytes(32, 'big')
        return selector + addr_bytes + amount_bytes
    
    def _settle_xrpl(self, config: SettlementConfig, receipts: List[ComputeReceipt]) -> List[str]:
        """Execute XRPL IOU payments."""
        tx_hashes = []
        
        for receipt in receipts:
            # XRPL Payment transaction with IOU
            # In production: use xrpl-py to submit Payment with IssuedCurrencyAmount
            
            tx_hash = f"XRPL_{secrets.token_hex(32)}"
            tx_hashes.append(tx_hash)
            
            logger.info(f"Simulated XRPL IOU payment: {receipt.reward_amount} AEGENTIX "
                       f"to {receipt.address} on XRPL")
        
        return tx_hashes
    
    def _settle_solana(self, config: SettlementConfig, receipts: List[ComputeReceipt]) -> List[str]:
        """Execute SPL Token transfers on Solana."""
        tx_hashes = []
        
        for receipt in receipts:
            # SPL Token transfer
            # In production: use solana-py to create transfer instruction
            
            tx_hash = f"SOL_{secrets.token_hex(32)}"
            tx_hashes.append(tx_hash)
            
            logger.info(f"Simulated SPL transfer: {receipt.reward_amount} AEGENTIX "
                       f"to {receipt.address} on Solana")
        
        return tx_hashes
    
    def _settle_cosmos(self, config: SettlementConfig, receipts: List[ComputeReceipt]) -> List[str]:
        """Execute IBC transfers on Cosmos."""
        tx_hashes = []
        
        for receipt in receipts:
            # IBC token transfer
            # In production: use cosmjs or similar
            
            tx_hash = f"COSMOS_{secrets.token_hex(32)}"
            tx_hashes.append(tx_hash)
            
            logger.info(f"Simulated IBC transfer: {receipt.reward_amount} AEGENTIX "
                       f"to {receipt.address} on Cosmos")
        
        return tx_hashes
    
    def _settle_bitcoin_l2(self, config: SettlementConfig, receipts: List[ComputeReceipt]) -> List[str]:
        """Execute SIP-010 transfers on Stacks/Bitcoin L2."""
        tx_hashes = []
        
        for receipt in receipts:
            # SIP-010 token transfer
            # In production: use stacks.js or similar
            
            tx_hash = f"STX_{secrets.token_hex(32)}"
            tx_hashes.append(tx_hash)
            
            logger.info(f"Simulated SIP-010 transfer: {receipt.reward_amount} AEGENTIX "
                       f"to {receipt.address} on Stacks")
        
        return tx_hashes


class SettlementMonitor:
    """Monitors settlement confirmations."""
    
    def __init__(self, vault: StatelessVault):
        self.vault = vault
        self.registry = get_chain_registry()
    
    def wait_for_confirmation(
        self,
        tx_hash: str,
        chain: str,
        confirmations: int = 1,
        timeout: int = 120
    ) -> bool:
        """Wait for transaction confirmation."""
        # In production: poll chain for confirmations
        # For now, simulate
        logger.info(f"Waiting for {confirmations} confirmations on {chain}: {tx_hash}")
        time.sleep(2)
        return True
    
    def verify_settlement(
        self,
        tx_hash: str,
        chain: str,
        expected_recipient: str,
        expected_amount: Decimal
    ) -> bool:
        """Verify settlement on-chain."""
        # In production: query chain for transaction details
        logger.info(f"Verifying settlement {tx_hash} on {chain}")
        return True


# Import needed modules
import secrets
from .engine import AEGENTIXStablecoin