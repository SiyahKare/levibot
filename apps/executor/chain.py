import os

from web3 import Web3

RPC = os.getenv("RPC_BASE_SEPOLIA")
CHAIN_ID = int(os.getenv("CHAIN_ID", "84532"))
w3 = Web3(Web3.HTTPProvider(RPC)) if RPC else None


def build_mock_data(orders):
    return "0x" + "11" * 32


def send_tx(session_pk: str, to: str, data: str, value: int = 0) -> str:
    if not w3:
        return "0xMOCK"
    acct = w3.eth.account.from_key(session_pk)
    tx = {
        "to": Web3.to_checksum_address(to),
        "value": value,
        "data": data,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "chainId": CHAIN_ID,
        "gas": 300000,
        "maxFeePerGas": w3.to_wei(20, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
        "type": 2,
    }
    signed = acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(signed.rawTransaction)
    return txh.hex()
