TICKERS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "ABEV3.SA",
    "MGLU3.SA",
    "WEGE3.SA",
    "RENT3.SA",
    "LREN3.SA",
    "SUZB3.SA",
]

PERIOD = "2y"           # período histórico a baixar
RSI_WINDOW = 14         # janela do RSI
SMA_SHORT = 20          # média móvel curta
SMA_LONG = 50           # média móvel longa
BOLLINGER_WINDOW = 20   # janela das Bandas de Bollinger

DATA_PATH = "data/processed/"
LOG_PATH = "pipeline.log"

# Horário de execução diária (após fechamento da B3: 18h BRT)
SCHEDULE_HOUR = 18
SCHEDULE_MINUTE = 30
