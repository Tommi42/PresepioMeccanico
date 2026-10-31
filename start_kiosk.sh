#!/bin/bash

# ==============================================================================
# Script di avvio automatico per Raspberry Pi (Kiosk Mode)
# ==============================================================================

# Percorso della cartella del progetto sul Raspberry Pi
# (Se lo script è dentro la cartella del progetto, individua il percorso in automatico)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. Attendi qualche secondo all'avvio per assicurare che Desktop e Rete siano pronti
sleep 3

# 2. Avvia il server Python in background (se non è già in esecuzione)
if ! pgrep -f "python3 server.py" > /dev/null; then
    python3 server.py &
fi

# 3. Attendi che il server locale sia pronto a rispondere
sleep 2

# 4. Rileva il browser Chromium installato su Raspberry Pi OS
if command -v chromium-browser &> /dev/null; then
    BROWSER="chromium-browser"
elif command -v chromium &> /dev/null; then
    BROWSER="chromium"
else
    # Fallback su xdg-open se Chromium non è presente
    xdg-open "http://localhost:8000" &
    exit 0
fi

# 5. Avvia Chromium a schermo intero (Kiosk Mode)
# --kiosk: Schermo intero senza barre, pulsanti né bordi
# --noerrdialogs: Non mostra finestre di errore
# --disable-infobars: Nasconde barre informative ("Ripristina schede", ecc.)
# --check-for-update-interval: Disattiva controlli aggiornamenti all'avvio
$BROWSER \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --check-for-update-interval=31536000 \
    http://localhost:8000
