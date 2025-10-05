from __future__ import annotations
import re
from ..ml.signal_model import infer

POS_PAT = re.compile(r"\b(buy|long)\b", re.I)
NEG_PAT = re.compile(r"\b(sell|short|exit all)\b", re.I)
NO_PAT = re.compile(r"\b(no trade|avoid|wait|sideline)\b", re.I)


def rule_vote(text: str):
    votes = {"BUY": 0, "SELL": 0, "NO-TRADE": 0}
    if POS_PAT.search(text):
        votes["BUY"] += 1
    if NEG_PAT.search(text):
        votes["SELL"] += 1
    if NO_PAT.search(text):
        votes["NO-TRADE"] += 1
    return votes


def score_signal(text: str):
    # rules
    rv = rule_vote(text)
    rule_label = max(rv, key=rv.get)
    rule_strength = rv[rule_label]

    # ml
    ml_label, ml_conf = infer(text)

    # fuse
    if rule_strength > 0 and ml_label != rule_label:
        # tie-break: if rule strong and ml_conf low, prefer rule
        final = rule_label if ml_conf < 0.8 else ml_label
    else:
        final = ml_label

    reasons = []
    if rule_strength > 0:
        reasons.append(f"rule:{rule_label}({rule_strength})")
    reasons.append(f"ml:{ml_label}({ml_conf:.2f})")

    # normalized confidence (0..1) quick proxy
    conf = min(0.99, 0.5 + 0.1 * rule_strength + min(0.49, ml_conf / 10))
    return {"label": final, "confidence": round(conf, 2), "reasons": reasons}



