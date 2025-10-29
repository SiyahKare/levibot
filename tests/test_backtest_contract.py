import numpy as np
import pandas as pd

from pkgs.signals import STRATEGIES


def dummy_df(n=200):
    rng = np.random.default_rng(42)
    price = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({"close": price})


def test_strategy_contract():
    df = dummy_df()
    eq, orders = STRATEGIES["sma"](df, fast=10, slow=50)
    assert len(eq) == len(df)
    assert isinstance(orders, list)
