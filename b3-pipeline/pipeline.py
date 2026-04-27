"""
pipeline.py — orquestrador principal do B3 Data Pipeline.

Uso:
    python pipeline.py              # executa uma vez agora
    python pipeline.py --schedule   # agenda execução diária
"""

import argparse
import logging
import sys
import time
from datetime import datetime

from config import LOG_PATH, SCHEDULE_HOUR, SCHEDULE_MINUTE, TICKERS, PERIOD
from collector.fetch import fetch_all
from processor.cleaner import clean
from processor.indicators import add_all
from storage.writer import save, save_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
logger = logging.getLogger("pipeline")


def run() -> dict:
    """Executa o pipeline completo e retorna métricas de execução."""
    start = time.time()
    logger.info("=" * 60)
    logger.info(f"PIPELINE INICIADO — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # 1. Coleta
        logger.info("[1/4] COLETA")
        raw_df = fetch_all(tickers=TICKERS, period=PERIOD)

        # 2. Limpeza
        logger.info("[2/4] LIMPEZA")
        clean_df = clean(raw_df)

        # 3. Enriquecimento
        logger.info("[3/4] INDICADORES")
        enriched_df = add_all(clean_df)

        # 4. Armazenamento
        logger.info("[4/4] ARMAZENAMENTO")
        data_path = save(enriched_df)
        summary_path = save_summary(enriched_df)

        elapsed = round(time.time() - start, 2)
        metrics = {
            "status": "success",
            "rows": len(enriched_df),
            "tickers": enriched_df["ticker"].nunique(),
            "columns": len(enriched_df.columns),
            "elapsed_sec": elapsed,
            "data_path": data_path,
            "summary_path": summary_path,
        }

        logger.info("=" * 60)
        logger.info(f"PIPELINE CONCLUÍDO em {elapsed}s")
        logger.info(f"  Linhas processadas : {metrics['rows']:,}")
        logger.info(f"  Tickers            : {metrics['tickers']}")
        logger.info(f"  Colunas geradas    : {metrics['columns']}")
        logger.info("=" * 60)

        return metrics

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        logger.error(f"PIPELINE FALHOU após {elapsed}s: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "elapsed_sec": elapsed}


def run_scheduled():
    """Mantém o processo rodando e executa diariamente no horário configurado."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        run,
        trigger="cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
        id="b3_pipeline",
    )

    logger.info(
        f"Scheduler iniciado — próxima execução às "
        f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} (horário de Brasília)"
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler encerrado pelo usuário.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B3 Data Pipeline")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Mantém o processo rodando com execução diária agendada",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        result = run()
        sys.exit(0 if result["status"] == "success" else 1)
