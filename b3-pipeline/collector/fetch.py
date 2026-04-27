import logging
import yfinance as yf
import pandas as pd
from config import TICKERS, PERIOD

logger = logging.getLogger(__name__)


def fetch_all(tickers: list = TICKERS, period: str = PERIOD) -> pd.DataFrame:
    """
    Baixa dados OHLCV de todos os tickers da B3 via yfinance.
    Retorna um DataFrame consolidado com coluna 'ticker'.
    """
    logger.info(f"Iniciando coleta: {len(tickers)} tickers | período: {period}")

    try:
        raw = yf.download(
            tickers,
            period=period,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"Erro ao baixar dados do yfinance: {e}")
        raise

    frames = []
    for ticker in tickers:
        try:
            df = raw[ticker].copy()
            df.dropna(how="all", inplace=True)

            if df.empty:
                logger.warning(f"Sem dados para {ticker}, pulando.")
                continue

            df["ticker"] = ticker
            df.reset_index(inplace=True)
            frames.append(df)
            logger.info(f"  {ticker}: {len(df)} linhas coletadas")

        except KeyError:
            logger.warning(f"Ticker {ticker} não encontrado na resposta.")
            continue

    if not frames:
        raise ValueError("Nenhum dado foi coletado. Verifique os tickers e a conexão.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Coleta concluída: {len(combined)} linhas no total")
    return combined
