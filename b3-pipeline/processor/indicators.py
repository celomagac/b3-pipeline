import logging
import pandas as pd
import numpy as np
from config import RSI_WINDOW, SMA_SHORT, SMA_LONG, BOLLINGER_WINDOW

logger = logging.getLogger(__name__)


def add_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula e adiciona todos os indicadores técnicos ao DataFrame.
    Todos os cálculos são feitos agrupados por ticker.
    """
    logger.info("Calculando indicadores técnicos...")

    df = df.copy()
    df = _moving_averages(df)
    df = _rsi(df)
    df = _bollinger_bands(df)
    df = _daily_return(df)
    df = _volume_avg(df)
    df = _signals(df)

    logger.info(f"Indicadores adicionados: {len(df.columns)} colunas no total")
    return df


def _moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    df[f"sma_{SMA_SHORT}"] = df.groupby("ticker")["Close"].transform(
        lambda x: x.rolling(SMA_SHORT, min_periods=1).mean().round(4)
    )
    df[f"sma_{SMA_LONG}"] = df.groupby("ticker")["Close"].transform(
        lambda x: x.rolling(SMA_LONG, min_periods=1).mean().round(4)
    )
    logger.info(f"  SMA {SMA_SHORT} e SMA {SMA_LONG} calculados")
    return df


def _rsi(df: pd.DataFrame) -> pd.DataFrame:
    def calc_rsi(series: pd.Series) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(RSI_WINDOW, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(RSI_WINDOW, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        return (100 - (100 / (1 + rs))).round(2)

    df[f"rsi_{RSI_WINDOW}"] = df.groupby("ticker")["Close"].transform(calc_rsi)
    logger.info(f"  RSI {RSI_WINDOW} calculado")
    return df


def _bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    def rolling_mean(x):
        return x.rolling(BOLLINGER_WINDOW, min_periods=1).mean()

    def rolling_std(x):
        return x.rolling(BOLLINGER_WINDOW, min_periods=1).std()

    mid = df.groupby("ticker")["Close"].transform(rolling_mean)
    std = df.groupby("ticker")["Close"].transform(rolling_std)

    df["bb_upper"] = (mid + 2 * std).round(4)
    df["bb_mid"] = mid.round(4)
    df["bb_lower"] = (mid - 2 * std).round(4)

    # % dentro das bandas (0 = fora inferior, 1 = fora superior)
    df["bb_pct"] = ((df["Close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])).round(4)

    logger.info(f"  Bandas de Bollinger ({BOLLINGER_WINDOW}) calculadas")
    return df


def _daily_return(df: pd.DataFrame) -> pd.DataFrame:
    df["daily_return"] = (
        df.groupby("ticker")["Close"]
        .pct_change()
        .mul(100)
        .round(4)
    )
    # Retorno acumulado no período
    df["cumulative_return"] = (
        df.groupby("ticker")["daily_return"]
        .transform(lambda x: (1 + x / 100).cumprod().sub(1).mul(100).round(4))
    )
    logger.info("  Retorno diário e acumulado calculados")
    return df


def _volume_avg(df: pd.DataFrame) -> pd.DataFrame:
    df["volume_sma_20"] = df.groupby("ticker")["Volume"].transform(
        lambda x: x.rolling(20, min_periods=1).mean().round(0).astype("int64")
    )
    # Razão volume atual / média (>1.5 = volume anormalmente alto)
    df["volume_ratio"] = (df["Volume"] / df["volume_sma_20"].replace(0, np.nan)).round(3)
    logger.info("  Volume médio e razão calculados")
    return df


def _signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sinais simples baseados nos indicadores:
    - golden_cross: SMA20 cruzou acima da SMA50 hoje
    - death_cross:  SMA20 cruzou abaixo da SMA50 hoje
    - rsi_oversold: RSI < 30
    - rsi_overbought: RSI > 70
    """
    sma_s = f"sma_{SMA_SHORT}"
    sma_l = f"sma_{SMA_LONG}"
    rsi_col = f"rsi_{RSI_WINDOW}"

    prev_sma_s = df.groupby("ticker")[sma_s].shift(1)
    prev_sma_l = df.groupby("ticker")[sma_l].shift(1)

    df["golden_cross"] = (df[sma_s] > df[sma_l]) & (prev_sma_s <= prev_sma_l)
    df["death_cross"] = (df[sma_s] < df[sma_l]) & (prev_sma_s >= prev_sma_l)
    df["rsi_oversold"] = df[rsi_col] < 30
    df["rsi_overbought"] = df[rsi_col] > 70

    logger.info("  Sinais de cruzamento e RSI calculados")
    return df
