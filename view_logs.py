#!/usr/bin/env python3
"""
Natalino - Visualizzatore & Esportatore di Log delle Conversazioni
=================================================================
Questo script permette di visualizzare, analizzare ed esportare i log
delle conversazioni con Natalino dal terminale o avviando un servizio
web dedicato sul proprio computer.

Utilizzo:
  python3 view_logs.py                     # Mostra riassunto e ultime conversazioni a terminale
  python3 view_logs.py -n 30               # Mostra le ultime 30 conversazioni
  python3 view_logs.py --search "mucca"    # Cerca conversazioni che contengono parole chiave
  python3 view_logs.py --today             # Mostra solo le conversazioni di oggi
  python3 view_logs.py --csv output.csv    # Esporta tutti i log in formato CSV per Excel
  python3 view_logs.py --json output.json  # Esporta tutti i log in formato JSON
  python3 view_logs.py --serve --port 8080 # Avvia un server web dedicato sul tuo computer
  python3 view_logs.py --remote http://IP_RASPBERRY:8000  # Legge i log da remoto
"""

import argparse
import csv
import datetime
import http.server
import json
import os
import socketserver
import sys
import urllib.parse
import urllib.request

DEFAULT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'conversations.jsonl')


def load_logs_from_file(file_path):
    if not os.path.exists(file_path):
        return []
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    records.reverse()
    return records


def load_logs_from_remote(remote_url):
    url = remote_url.rstrip('/') + '/api/logs?limit=all'
    req = urllib.request.Request(url, headers={'User-Agent': 'NatalinoLogViewer/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data.get('logs', [])


def filter_logs(records, search=None, only_today=False, source=None):
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    filtered = []
    for r in records:
        if only_today:
            ts = r.get('datetime_local') or r.get('timestamp') or ''
            if today_str not in ts:
                continue

        if source == 'openai' and not r.get('isFromOpenAi'):
            continue
        if source == 'fallback' and (r.get('isFromOpenAi') or r.get('errorNote')):
            continue
        if source == 'error' and not r.get('errorNote'):
            continue

        if search:
            s = search.lower()
            q = (r.get('question') or '').lower()
            a = (r.get('answer') or '').lower()
            if s not in q and s not in a:
                continue

        filtered.append(r)
    return filtered


def print_terminal_view(records, limit=15):
    total = len(records)
    openai_count = sum(1 for r in records if r.get('isFromOpenAi'))
    fallback_count = total - openai_count
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for r in records if today_str in (r.get('datetime_local') or r.get('timestamp') or ''))

    print("\n" + "=" * 70)
    print(" 🌟 NATALINO — REGISTRO CONVERSAZIONI DEL PRESEPIO")
    print("=" * 70)
    print(f" 📊 Totale registrato: {total}")
    print(f" 📅 Oggi:              {today_count}")
    if total > 0:
        print(f" 🤖 OpenAI:            {openai_count} ({round(openai_count/total*100)}%)")
        print(f" 💾 Riserva locale:    {fallback_count} ({round(fallback_count/total*100)}%)")
    print("=" * 70 + "\n")

    display_records = records[:limit]
    if not display_records:
        print(" (Nessuna conversazione corrispondente trovata)\n")
        return

    for i, r in enumerate(display_records, 1):
        time_str = r.get('datetime_local') or r.get('timestamp') or 'N/D'
        is_ai = r.get('isFromOpenAi', False)
        source_label = f"OpenAI ({r.get('model', 'gpt-4o-mini')})" if is_ai else "Riserva Locale"
        dur_str = f" [{r.get('durationMs', 0)/1000:.1f}s]" if r.get('durationMs') else ""
        err = r.get('errorNote')

        print(f" [{i}] {time_str} | {source_label}{dur_str}")
        print(f"     ❓ Domanda: «{r.get('question', '')}»")
        answer = r.get('answer', '')
        if len(answer) > 140:
            answer = answer[:137] + "..."
        print(f"     💬 Risposta: {answer}")
        if err:
            print(f"     ⚠️  Errore: {err}")
        print("-" * 70)

    if total > limit:
        print(f" ... e altre {total - limit} conversazioni più vecchie.")
        print(f" Usa '-n {total}' per vederle tutte, o '--serve' per aprirle nel browser.\n")


def export_csv(records, filename):
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        # BOM per Excel
        f.write('\ufeff')
        writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['ID', 'Data e Ora', 'Domanda', 'Risposta', 'Origine', 'Modello', 'Durata (ms)', 'Errori'])
        for r in records:
            orig = 'OpenAI' if r.get('isFromOpenAi') else 'Riserva Locale'
            writer.writerow([
                r.get('id', ''),
                r.get('datetime_local', '') or r.get('timestamp', ''),
                (r.get('question') or '').replace('\n', ' '),
                (r.get('answer') or '').replace('\n', ' '),
                orig,
                r.get('model', ''),
                r.get('durationMs', ''),
                r.get('errorNote', '') or ''
            ])
    print(f"✅ File CSV esportato con successo in: {filename}")


def export_json(records, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✅ File JSON esportato con successo in: {filename}")


def run_standalone_server(port, get_logs_fn):
    class ViewerHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/logs':
                logs = get_logs_fn()
                today_str = datetime.datetime.now().strftime('%Y-%m-%d')
                stats = {
                    'total': len(logs),
                    'today': sum(1 for r in logs if today_str in (r.get('datetime_local') or r.get('timestamp') or '')),
                    'openaiCount': sum(1 for r in logs if r.get('isFromOpenAi')),
                    'fallbackCount': sum(1 for r in logs if not r.get('isFromOpenAi')),
                    'avgDurationMs': round(sum(r.get('durationMs', 0) for r in logs if r.get('durationMs')) / max(1, sum(1 for r in logs if r.get('durationMs'))))
                }
                res = json.dumps({'status': 'ok', 'logs': logs, 'stats': stats}, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(res)
                return

            if parsed.path in ('/api/logs/export.csv', '/export.csv'):
                logs = get_logs_fn()
                output = io.StringIO()
                output.write('\ufeff')
                writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['ID', 'Data e Ora', 'Domanda', 'Risposta', 'Origine', 'Modello', 'Durata (ms)', 'Errori'])
                for r in logs:
                    orig = 'OpenAI' if r.get('isFromOpenAi') else 'Riserva Locale'
                    writer.writerow([
                        r.get('id', ''),
                        r.get('datetime_local', '') or r.get('timestamp', ''),
                        (r.get('question') or '').replace('\n', ' '),
                        (r.get('answer') or '').replace('\n', ' '),
                        orig,
                        r.get('model', ''),
                        r.get('durationMs', ''),
                        r.get('errorNote', '') or ''
                    ])
                csv_bytes = output.getvalue().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="conversazioni_natalino.csv"')
                self.end_headers()
                self.wfile.write(csv_bytes)
                return

            # Importa DASHBOARD_HTML da server.py se disponibile, o fallback
            try:
                from server import DASHBOARD_HTML
                html = DASHBOARD_HTML
            except Exception:
                html = "<h1>Natalino Logs Server</h1><p>API attiva su /api/logs</p>"

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', port), ViewerHandler) as httpd:
        print(f"🚀 Visualizzatore Log Natalino avviato su http://localhost:{port}")
        print("Premi CTRL+C per terminare.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArresto server.")


def main():
    parser = argparse.ArgumentParser(description="Natalino - Visualizzatore & Esportatore di Log")
    parser.add_argument('-n', '--limit', type=int, default=15, help="Numero di conversazioni da mostrare a terminale (default: 15)")
    parser.add_argument('-s', '--search', type=str, default=None, help="Cerca testo nelle domande o risposte")
    parser.add_argument('--today', action='store_true', help="Mostra solo le conversazioni di oggi")
    parser.add_argument('--source', choices=['openai', 'fallback', 'error'], default=None, help="Filtra per origine risposta")
    parser.add_argument('--csv', type=str, default=None, help="Esporta i log filtrati in un file CSV per Excel")
    parser.add_argument('--json', type=str, default=None, help="Esporta i log filtrati in un file JSON")
    parser.add_argument('--file', type=str, default=DEFAULT_LOG_PATH, help="Percorso del file conversations.jsonl")
    parser.add_argument('--remote', type=str, default=None, help="URL del server Natalino remoto (es. http://192.168.1.50:8000)")
    parser.add_argument('--serve', action='store_true', help="Avvia il servizio web con interfaccia grafica sul browser")
    parser.add_argument('--port', type=int, default=8080, help="Porta per la modalità --serve (default: 8080)")

    args = parser.parse_args()

    def fetch_records():
        if args.remote:
            records = load_logs_from_remote(args.remote)
        else:
            records = load_logs_from_file(args.file)
        return filter_logs(records, search=args.search, only_today=args.today, source=args.source)

    if args.serve:
        run_standalone_server(args.port, fetch_records)
        return

    records = fetch_records()

    if args.csv:
        export_csv(records, args.csv)
        return

    if args.json:
        export_json(records, args.json)
        return

    print_terminal_view(records, limit=args.limit)


if __name__ == '__main__':
    main()
