# B3 Data Pipeline

Pipeline de dados financeiros para coleta, limpeza, enriquecimento e armazenamento de cotações da B3 (Bolsa de Valores brasileira).

## Visão geral

```
yfinance → Pandas (limpeza) → Indicadores técnicos → Parquet particionado
```

O pipeline roda diariamente após o fechamento do mercado e processa **~5.000 linhas por execução** (10 tickers × ~2 anos de histórico). Os dados são salvos em formato Parquet particionado por ticker, o que permite consultas rápidas por ativo sem carregar todo o dataset.

## Tickers monitorados

PETR4, VALE3, ITUB4, BBDC4, ABEV3, MGLU3, WEGE3, RENT3, LREN3, SUZB3

## Tecnologias

| Ferramenta | Uso |
|---|---|
| `yfinance` | Coleta de dados OHLCV via Yahoo Finance |
| `pandas` | Limpeza, transformação e cálculo de indicadores |
| `pyarrow` | Serialização em formato Parquet com compressão Snappy |
| `APScheduler` | Agendamento da execução diária |
| `matplotlib` | Geração de gráficos de análise |

## Estrutura do projeto

```
b3-pipeline/
├── collector/
│   └── fetch.py          # coleta paralela via yfinance
├── processor/
│   ├── cleaner.py        # limpeza e validação dos dados
│   └── indicators.py     # SMA, RSI, Bollinger Bands, sinais
├── storage/
│   └── writer.py         # leitura e escrita em Parquet
├── pipeline.py           # orquestrador principal
├── analysis.py           # análise exploratória e gráficos
├── config.py             # configurações centralizadas
├── requirements.txt
└── data/
    └── processed/        # saída: .parquet + summary.csv + gráficos
```

## Como executar

```bash
# 1. Clone e instale as dependências
git clone https://github.com/seu-usuario/b3-pipeline.git
cd b3-pipeline
pip install -r requirements.txt

# 2. Execute o pipeline uma vez
python pipeline.py

# 3. Gere os gráficos de análise
python analysis.py

# 4. (Opcional) Agende a execução diária às 18h30 BRT
python pipeline.py --schedule
```

## Indicadores calculados

| Indicador | Descrição |
|---|---|
| `sma_20` / `sma_50` | Médias móveis simples de 20 e 50 períodos |
| `rsi_14` | Índice de Força Relativa (14 períodos) |
| `bb_upper/mid/lower` | Bandas de Bollinger (20 períodos, 2σ) |
| `bb_pct` | Posição relativa do preço dentro das bandas |
| `daily_return` | Variação percentual diária |
| `cumulative_return` | Retorno acumulado no período |
| `volume_sma_20` | Média móvel do volume (20 dias) |
| `volume_ratio` | Razão volume atual / média (>1.5 = volume anormal) |
| `golden_cross` | SMA20 cruzou acima da SMA50 |
| `death_cross` | SMA20 cruzou abaixo da SMA50 |
| `rsi_oversold` | RSI < 30 (sobrevendido) |
| `rsi_overbought` | RSI > 70 (sobrecomprado) |

## Decisões técnicas

**Por que Parquet e não CSV?**
Parquet é o formato padrão de pipelines de dados em produção. Ele comprime automaticamente (Snappy), preserva tipos de dados sem perda e suporta leitura de colunas específicas sem carregar o arquivo inteiro. Carregar apenas PETR4 nesse projeto é ~10x mais rápido do que ler um CSV consolidado.

**Por que particionar por ticker?**
O particionamento físico (uma pasta por ticker) permite que o pyarrow filtre no sistema de arquivos antes de deserializar qualquer dado. Em datasets maiores, isso passa de segundos para milissegundos na leitura.

**Por que APScheduler e não cron?**
Portabilidade. Cron é específico de Linux/macOS. APScheduler roda no mesmo processo Python em qualquer sistema operacional, mantendo o projeto auto-contido.

## Saída do pipeline

```
2024-10-15 18:30:01 | INFO     | pipeline | PIPELINE INICIADO
2024-10-15 18:30:01 | INFO     | pipeline | [1/4] COLETA
2024-10-15 18:30:04 | INFO     | collector.fetch | PETR4.SA: 502 linhas coletadas
...
2024-10-15 18:30:05 | INFO     | pipeline | [2/4] LIMPEZA
2024-10-15 18:30:05 | INFO     | pipeline | [3/4] INDICADORES
2024-10-15 18:30:05 | INFO     | pipeline | [4/4] ARMAZENAMENTO
2024-10-15 18:30:06 | INFO     | pipeline | PIPELINE CONCLUÍDO em 4.83s
2024-10-15 18:30:06 | INFO     | pipeline |   Linhas processadas : 5.020
2024-10-15 18:30:06 | INFO     | pipeline |   Tickers            : 10
2024-10-15 18:30:06 | INFO     | pipeline |   Colunas geradas    : 19
```

## Possíveis extensões

- Armazenar em PostgreSQL ou DuckDB para queries SQL
- Adicionar alertas por e-mail quando golden/death cross ocorrer
- Expor os dados via FastAPI para consumo por um frontend
- Integrar com Great Expectations para validação de qualidade de dados
