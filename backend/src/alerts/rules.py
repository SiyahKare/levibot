from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

Op = Literal[
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "regex",
    "contains",
    "startswith",
    "endswith",
]


def _get(d: dict[str, Any], path: str, default=None):
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


OPS: dict[Op, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "gt": lambda a, b: (a is not None and b is not None and a > b),
    "gte": lambda a, b: (a is not None and b is not None and a >= b),
    "lt": lambda a, b: (a is not None and b is not None and a < b),
    "lte": lambda a, b: (a is not None and b is not None and a <= b),
    "in": lambda a, b: a in (b or []),
    "contains": lambda a, b: isinstance(a, str)
    and isinstance(b, str)
    and b.lower() in a.lower(),
    "startswith": lambda a, b: isinstance(a, str)
    and isinstance(b, str)
    and a.lower().startswith(b.lower()),
    "endswith": lambda a, b: isinstance(a, str)
    and isinstance(b, str)
    and a.lower().endswith(b.lower()),
    "regex": lambda a, b: isinstance(a, str) and bool(re.search(b, a or "")),
}


@dataclass
class Condition:
    field: str
    op: Op
    value: Any

    def eval(self, event: dict[str, Any]) -> bool:
        a = _get(event, self.field)
        return OPS[self.op](a, self.value)


@dataclass
class AlertRule:
    id: str
    name: str
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    any: list[Condition] = field(default_factory=list)  # at least one must pass
    all: list[Condition] = field(default_factory=list)  # all must pass
    enabled: bool = True
    target: str | None = None  # "slack" | "discord" | "webhook:<url>" (PR-36 için)
    template: str | None = None  # string template (PR-36 için)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AlertRule:
        def to_conds(items):
            return [
                Condition(field=i["field"], op=i["op"], value=i.get("value"))
                for i in (items or [])
            ]

        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            severity=d.get("severity", "info"),
            any=to_conds(d.get("any", [])),
            all=to_conds(d.get("all", [])),
            enabled=d.get("enabled", True),
            target=d.get("target"),
            template=d.get("template"),
        )

    def matches(self, event: dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        if self.all and not all(c.eval(event) for c in self.all):
            return False
        if self.any:
            return any(c.eval(event) for c in self.any)
        # if no ANY provided, ALL already passed → match
        return True


def load_rules(path: str | Path) -> list[AlertRule]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [AlertRule.from_dict(x) for x in data.get("rules", []) if x.get("id")]


def evaluate(event: dict[str, Any], rules: list[AlertRule]) -> list[AlertRule]:
    """Return list of matching rules for a given event record."""
    return [r for r in rules if r.matches(event)]


def pretty(event: dict[str, Any]) -> str:
    try:
        return json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(event)
