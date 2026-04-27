"""
analysis.py — análise exploratória dos dados processados.

Execute após rodar pipeline.py pelo menos uma vez.
Gera gráficos e imprime um resumo das métricas no terminal.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from storage.writer import load
from config import DATA_PATH

plt.style.use("seaborn-v0_8-whitegrid")
COLORS = ["#2563EB", "#DC2626", "#16A34A", "#D97706", "#7C3AED",
          "#0891B2", "#BE185D", "#65A30D", "#EA580C", "#4338CA"]


def print_summary():
    """Imprime resumo estatístico de todos os tickers."""
    df = load()
    rsi_col = next((c for c in df.columns if c.startswith("rsi_")), "rsi_14")

    print("\n" + "=" * 70)
    print("RESUMO — ÚLTIMOS DADOS DISPONÍVEIS POR TICKER")
    print("=" * 70)

    latest = df.sort_values("Date").groupby("ticker").last().reset_index()
    cols = ["ticker", "Close", "daily_return", "cumulative_return", rsi_col, "volume_ratio"]
    cols = [c for c in cols if c in latest.columns]

    print(latest[cols].to_string(index=False, float_format="{:.2f}".format))
    print("=" * 70)

    print("\nSINAIS ATIVOS:")
    if "golden_cross" in df.columns:
        crosses = latest[latest["golden_cross"] == True]["ticker"].tolist()
        if crosses:
            print(f"  Golden Cross : {', '.join(crosses)}")

    if "death_cross" in df.columns:
        crosses = latest[latest["death_cross"] == True]["ticker"].tolist()
        if crosses:
            print(f"  Death Cross  : {', '.join(crosses)}")

    if "rsi_oversold" in df.columns:
        oversold = latest[latest["rsi_oversold"] == True]["ticker"].tolist()
        if oversold:
            print(f"  RSI Oversold (<30) : {', '.join(oversold)}")

    if "rsi_overbought" in df.columns:
        overbought = latest[latest["rsi_overbought"] == True]["ticker"].tolist()
        if overbought:
            print(f"  RSI Overbought (>70) : {', '.join(overbought)}")


def plot_prices():
    """Gráfico de preços normalizados (base 100) para comparar tickers."""
    df = load()
    tickers = df["ticker"].unique().tolist()

    fig, ax = plt.subplots(figsize=(12, 5))

    for i, ticker in enumerate(tickers):
        sub = df[df["ticker"] == ticker].set_index("Date")["Close"]
        normalized = (sub / sub.iloc[0]) * 100
        ax.plot(normalized, label=ticker.replace(".SA", ""), color=COLORS[i % len(COLORS)], linewidth=1.5)

    ax.set_title("Retorno normalizado (base 100) — B3", fontsize=14, pad=12)
    ax.set_ylabel("Índice (base 100)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    ax.legend(ncol=5, fontsize=9, loc="upper left")
    plt.tight_layout()
    plt.savefig("data/processed/prices_normalized.png", dpi=150)
    print("\nGráfico salvo: data/processed/prices_normalized.png")
    plt.show()


def plot_rsi(ticker: str = "PETR4.SA"):
    """Gráfico de preço + RSI para um ticker específico."""
    df = load(ticker=ticker)
    rsi_col = next((c for c in df.columns if c.startswith("rsi_")), None)
    if not rsi_col:
        print("RSI não encontrado nos dados.")
        return

    df = df.set_index("Date").last("180D")   # últimos 6 meses

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

    # Painel de preço
    ax1.plot(df["Close"], color="#2563EB", linewidth=1.5, label="Preço")
    if "sma_20" in df.columns:
        ax1.plot(df["sma_20"], color="#F59E0B", linewidth=1, linestyle="--", label="SMA20")
    if "sma_50" in df.columns:
        ax1.plot(df["sma_50"], color="#DC2626", linewidth=1, linestyle="--", label="SMA50")
    if "bb_upper" in df.columns:
        ax1.fill_between(df.index, df["bb_lower"], df["bb_upper"], alpha=0.1, color="#2563EB", label="Bollinger")
    ax1.set_title(f"{ticker.replace('.SA', '')} — Preço + Indicadores (últimos 6 meses)", fontsize=13)
    ax1.set_ylabel("Preço (R$)")
    ax1.legend(fontsize=9)

    # Painel RSI
    ax2.plot(df[rsi_col], color="#7C3AED", linewidth=1.5)
    ax2.axhline(70, color="#DC2626", linestyle="--", linewidth=0.8, alpha=0.7)
    ax2.axhline(30, color="#16A34A", linestyle="--", linewidth=0.8, alpha=0.7)
    ax2.fill_between(df.index, df[rsi_col], 70, where=(df[rsi_col] > 70), alpha=0.2, color="#DC2626")
    ax2.fill_between(df.index, df[rsi_col], 30, where=(df[rsi_col] < 30), alpha=0.2, color="#16A34A")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))

    plt.tight_layout()
    out_path = f"data/processed/{ticker.replace('.SA', '')}_rsi.png"
    plt.savefig(out_path, dpi=150)
    print(f"Gráfico salvo: {out_path}")
    plt.show()


def plot_correlation():
    """Mapa de correlação dos retornos diários entre os tickers."""
    df = load()
    pivot = df.pivot_table(index="Date", columns="ticker", values="daily_return")
    pivot.columns = [c.replace(".SA", "") for c in pivot.columns]
    corr = pivot.corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, shrink=0.8)

    tickers_clean = corr.columns.tolist()
    ax.set_xticks(range(len(tickers_clean)))
    ax.set_yticks(range(len(tickers_clean)))
    ax.set_xticklabels(tickers_clean, rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels(tickers_clean, fontsize=10)

    for i in range(len(tickers_clean)):
        for j in range(len(tickers_clean)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8,
                    color="black" if abs(corr.iloc[i, j]) < 0.7 else "white")

    ax.set_title("Correlação dos retornos diários — B3", fontsize=13, pad=12)
    plt.tight_layout()
    plt.savefig("data/processed/correlation.png", dpi=150)
    print("Gráfico salvo: data/processed/correlation.png")
    plt.show()


if __name__ == "__main__":
    print_summary()
    plot_prices()
    plot_rsi("PETR4.SA")
    plot_correlation()
