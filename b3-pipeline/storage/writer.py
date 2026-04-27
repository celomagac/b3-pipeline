import logging
import os
import pandas as pd
from datetime import datetime
from config import DATA_PATH

logger = logging.getLogger(__name__)


def save(df: pd.DataFrame, path: str = DATA_PATH) -> str:
    """
    Salva o DataFrame em formato Parquet particionado por ticker.
    Retorna o caminho onde foi salvo.
    """
    os.makedirs(path, exist_ok=True)

    df.to_parquet(
        path,
        partition_cols=["ticker"],
        index=False,
        engine="pyarrow",
        compression="snappy",   # compressão rápida, padrão em pipelines reais
    )

    logger.info(f"Dados salvos em Parquet particionado: {path}")
    return path


def save_summary(df: pd.DataFrame, path: str = DATA_PATH) -> str:
    """
    Gera e salva um CSV de resumo com as métricas mais recentes de cada ticker.
    Útil para dashboards ou para uma rápida conferência visual.
    """
    rsi_col = next((c for c in df.columns if c.startswith("rsi_")), None)
    sma_s = next((c for c in df.columns if c.startswith("sma_2")), None)
    sma_l = next((c for c in df.columns if c.startswith("sma_5")), None)

    agg = {
        "Close": "last",
        "daily_return": "last",
        "cumulative_return": "last",
        "Volume": "last",
        "volume_ratio": "last",
    }
    if rsi_col:
        agg[rsi_col] = "last"
    if sma_s:
        agg[sma_s] = "last"
    if sma_l:
        agg[sma_l] = "last"
    if "golden_cross" in df.columns:
        agg["golden_cross"] = "last"
        agg["death_cross"] = "last"

    summary = df.groupby("ticker").agg(agg).reset_index()
    summary["updated_at"] = datetime.utcnow().isoformat()

    summary_path = os.path.join(path, "summary.csv")
    summary.to_csv(summary_path, index=False)
    logger.info(f"Resumo salvo em: {summary_path}")
    return summary_path


def load(ticker: str = None, path: str = DATA_PATH) -> pd.DataFrame:
    import pyarrow.dataset as ds

    if ticker:
        ticker_path = os.path.join(path, f"ticker={ticker}")
        if not os.path.exists(ticker_path):
            raise FileNotFoundError(f"Dados não encontrados para {ticker} em {ticker_path}")
        df = pd.read_parquet(ticker_path, engine="pyarrow")
        df["ticker"] = ticker
    else:
        dataset = ds.dataset(path, format="parquet", partitioning="hive",
                             exclude_invalid_files=True)
        df = dataset.to_table().to_pandas()

    logger.info(f"Dados carregados: {len(df)} linhas")
    return df