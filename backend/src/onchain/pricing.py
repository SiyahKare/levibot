from __future__ import annotations

from web3 import Web3


QUOTER_V2 = Web3.to_checksum_address("0x61fFE014bA17989E743c5F6cB21bF9697530B21e")
USDC = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
WETH = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
FEE_500 = 500


def eth_usd_price(w3: Web3) -> float:
    """Returns approximate ETH/USD using Uniswap v3 QuoterV2 (WETH->USDC, 0.05%)."""
    fn = w3.eth.contract(QUOTER_V2, abi=[
        {
            "name": "quoteExactInputSingle",
            "type": "function",
            "stateMutability": "view",
            "inputs": [
                {
                    "name": "params",
                    "type": "tuple",
                    "components": [
                        {"name": "tokenIn", "type": "address"},
                        {"name": "tokenOut", "type": "address"},
                        {"name": "fee", "type": "uint24"},
                        {"name": "amountIn", "type": "uint256"},
                        {"name": "sqrtPriceLimitX96", "type": "uint160"},
                    ],
                }
            ],
            "outputs": [{"name": "amountOut", "type": "uint256"}],
        }
    ]).functions
    out = fn.quoteExactInputSingle((WETH, USDC, FEE_500, 10 ** 18, 0)).call()
    return float(out) / 1e6


__all__ = ["eth_usd_price", "WETH", "USDC", "FEE_500"]













