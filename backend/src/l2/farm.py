from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from ..infra.logger import JsonlEventLogger


@dataclass
class Wallet:
    id: str  # filename stem or custom id
    address: str
    label: str | None = None
    networks: list[str] | None = None


class WalletRegistry:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("backend/wallets")
        self._wallets: dict[str, Wallet] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.root.exists():
            return
        for p in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(p.read_text())
                w = Wallet(
                    id=p.stem,
                    address=data.get("address", ""),
                    label=data.get("label"),
                    networks=data.get("networks") or ["zksync", "starknet", "blast"],
                )
                if w.address:
                    self._wallets[w.id] = w
            except Exception:
                continue

    def list(self) -> dict[str, dict]:
        self._load()
        return {k: asdict(v) for k, v in self._wallets.items()}

    def get(self, wallet_id: str) -> Wallet | None:
        self._load()
        return self._wallets.get(wallet_id)


class L2Farmer:
    def __init__(self, registry: WalletRegistry | None = None) -> None:
        self.registry = registry or WalletRegistry()
        self.logger = JsonlEventLogger()

    def simulate_action(
        self,
        wallet_id: str,
        network: str,
        protocol: str,
        action: str,
        amount: float | None = None,
        dry_run: bool = True,
        extra: dict | None = None,
    ) -> dict:
        w = self.registry.get(wallet_id)
        if not w:
            return {"ok": False, "error": "wallet_not_found", "wallet_id": wallet_id}
        payload = {
            "wallet_id": wallet_id,
            "address": w.address,
            "network": network,
            "protocol": protocol,
            "action": action,
            "amount": amount,
            "dry_run": dry_run,
            "ts": time.time(),
        }
        if extra:
            payload["extra"] = extra
        self.logger.write("L2_ACTIVITY", payload)
        # Gerçek zincir entegrasyonları ileride eklenecek; şimdilik log + echo
        return {"ok": True, "wallet": asdict(w), "activity": payload}

    def run_sequence(
        self,
        wallet_id: str,
        network: str,
        recipe: str = "default",
        dry_run: bool = True,
    ) -> dict:
        seq_map: dict[str, list[dict]] = {
            "zksync": [
                {"protocol": "syncswap", "action": "swap", "amount": 10.0},
                {"protocol": "mute", "action": "lp_add", "amount": 5.0},
                {"protocol": "zkns", "action": "register", "amount": 0.02},
            ],
            "starknet": [
                {"protocol": "starknetid", "action": "register", "amount": 0.02},
                {"protocol": "mySwap", "action": "swap", "amount": 10.0},
            ],
            "blast": [
                {"protocol": "thruster", "action": "swap", "amount": 10.0},
                {"protocol": "juice", "action": "stake", "amount": 5.0},
            ],
        }
        steps = seq_map.get(network.lower(), [])
        results = []
        for s in steps:
            res = self.simulate_action(
                wallet_id=wallet_id,
                network=network,
                protocol=s["protocol"],
                action=s["action"],
                amount=s.get("amount"),
                dry_run=dry_run,
            )
            results.append(res)
        return {"ok": True, "count": len(results), "results": results}


REGISTRY = WalletRegistry()
FARMER = L2Farmer(REGISTRY)
