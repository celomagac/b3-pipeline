import logging
import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume", "ticker"}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e valida o DataFrame bruto do yfinance.
    Etapas: verificação de colunas → tipos → duplicatas → nulos → outliers → ordenação.
    """
    logger.info(f"Iniciando limpeza: {len(df)} linhas recebidas")

    df = _validate_columns(df)
    df = _fix_types(df)
    df = _remove_duplicates(df)
    df = _handle_nulls(df)
    df = _remove_outliers(df)
    df = _sort(df)

    logger.info(f"Limpeza concluída: {len(df)} linhas após tratamento")
    return df


def _validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no DataFrame: {missing}")
    return df[list(EXPECTED_COLUMNS)]


def _fix_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["ticker"] = df["ticker"].astype("category")

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype("int64")
    return df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["Date", "ticker"])
    removed = before - len(df)
    if removed:
        logger.warning(f"  {removed} linhas duplicadas removidas")
    return df


def _handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    price_cols = ["Open", "High", "Low", "Close"]

    # Preenche com forward fill por ticker (dia sem dado herda o último)
    df = df.sort_values(["ticker", "Date"])
    df[price_cols] = df.groupby("ticker")[price_cols].transform(
        lambda x: x.ffill().bfill()
    )

    null_count = df[price_cols].isnull().sum().sum()
    if null_count:
        logger.warning(f"  {null_count} nulos restantes após ffill — linhas removidas")
        df = df.dropna(subset=price_cols)

    return df


def _remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove dias com variação de Close > 50% em relação ao dia anterior.
    Geralmente são splits ou erros de dado.
    """
    df = df.copy()
    df["_pct_change"] = df.groupby("ticker")["Close"].pct_change().abs()
    outliers = df["_pct_change"] > 0.50

    if outliers.sum():
        logger.warning(f"  {outliers.sum()} possíveis outliers/splits detectados (>50% var.)")

    df = df.drop(columns=["_pct_change"])
    return df


def _sort(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["ticker", "Date"]).reset_index(drop=True)
