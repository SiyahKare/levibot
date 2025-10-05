from __future__ import annotations

import asyncio
import datetime as dt
import os
from typing import Optional

from web3 import Web3
from web3._utils.filters import LogFilter

from ..infra.logger import log_event


UNISWAP_V3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
TOPIC_POOL_CREATED = Web3.keccak(text="PoolCreated(address,address,uint24,int24,address)").hex()
TOPIC_TRANSFER = Web3.keccak(text="Transfer(address,address,uint256)").hex()


async def run(chain_name: str, ws_url: str) -> None:
    w3 = Web3(Web3.WebsocketProvider(ws_url))
    if not w3.is_connected():
        raise RuntimeError("WS connect fail")

    pool_f: LogFilter = w3.eth.filter({"address": UNISWAP_V3_FACTORY, "topics": [TOPIC_POOL_CREATED]})
    xfer_f: LogFilter = w3.eth.filter({"topics": [TOPIC_TRANSFER]})

    print(f"[{chain_name}] on-chain listener up")
    while True:
        for ev in pool_f.get_new_entries():
            log_event(
                "ONCHAIN_SIGNAL",
                {
                    "chain": chain_name,
                    "kind": "univ3_pool_created",
                    "tx_hash": ev["transactionHash"].hex(),
                    "block": ev["blockNumber"],
                    "ts": dt.datetime.utcnow().isoformat() + "Z",
                },
            )
        for ev in xfer_f.get_new_entries():
            log_event(
                "ONCHAIN_SIGNAL",
                {
                    "chain": chain_name,
                    "kind": "erc20_transfer",
                    "tx_hash": ev["transactionHash"].hex(),
                    "block": ev["blockNumber"],
                },
            )
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run("ethereum", os.getenv("ETH_WS", "")))













