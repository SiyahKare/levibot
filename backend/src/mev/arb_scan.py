from __future__ import annotations

import duckdb as d
import networkx as nx
from typing import List

from ..infra.logger import log_event


def scan_once(symbols: List[str]) -> None:
    rows = d.sql(
        """
      SELECT 'uniswapv3' AS dex, symbol, close AS px FROM read_parquet('backend/data/parquet/dex/univ3_prices.parquet')
      UNION ALL
      SELECT 'sushiswap', symbol, px FROM read_parquet('backend/data/parquet/dex/sushi_prices.parquet')
    """
    ).df()
    if rows.empty:
        return
    for sym in symbols:
        g = nx.DiGraph()
        ss = rows[rows.symbol == sym]
        for _, a in ss.iterrows():
            for _, b in ss.iterrows():
                if a.dex == b.dex:
                    continue
                edge_bps = (b.px - a.px) / ((a.px + b.px) / 2) * 1e4
                g.add_edge(a.dex, b.dex, bps=edge_bps)
        edges = list(g.edges(data=True))
        if not edges:
            continue
        best = max((d for _, _, d in edges), key=lambda e: e["bps"], default=None)
        if not best or best["bps"] < 8:
            continue
        log_event("MEV_ARB_OPP", {"symbol": sym, "edge_bps": round(best["bps"], 2), "route": [best]})


__all__ = ["scan_once"]













