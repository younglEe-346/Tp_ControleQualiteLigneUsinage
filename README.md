# TP1 : Contrôle qualité d'une ligne d'usinage

ENSAM Casablanca, Programmation Avancée (Python), 2026-2027.

Programme qui lit les mesures d'un palpeur, décide si chaque pièce est
conforme, à reprendre ou rebut, calcule Cp/Cpk et imprime un rapport.

## Lancer

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pytest
    python main.py