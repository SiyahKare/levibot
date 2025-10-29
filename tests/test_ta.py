import numpy as np

from pkgs.signals.ta import sma


def test_sma_len():
    x = np.arange(10, dtype=float)
    y = sma(x, 3)
    assert len(y) == 10 and not np.isnan(y[-1])
