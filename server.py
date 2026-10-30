import http.server
import json
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIRECTORY = os.path.join(os.path.dirname(__file__), 'dist')

if not os.path.isdir(DIRECTORY):
    print(f"Errore: la cartella '{DIRECTORY}' non esiste.")
    print("Esegui prima il comando: npm run build")
    sys.exit(1)

def get_configured_api_key():
    # 1. Variabile d'ambiente
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if api_key:
        return api_key

    # 2. File api_key.txt nella cartella principale
    key_file = os.path.join(os.path.dirname(__file__), 'api_key.txt')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    # 3. File config.json (in dist/ o nella cartella principale)
    for c_path in [
        os.path.join(DIRECTORY, 'config.json'),
        os.path.join(os.path.dirname(__file__), 'config.json'),
    ]:
        if os.path.exists(c_path):
            try:
                with open(c_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key = data.get('openaiApiKey', '').strip()
                    if key:
                        return key
            except Exception:
                pass

    return ''

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Endpoint di configurazione dinamica a runtime
        clean_path = self.path.split('?')[0]
        if clean_path in ('/api/config', '/config.json'):
            api_key = get_configured_api_key()
            response_data = json.dumps({'openaiApiKey': api_key}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(response_data)
            return

        # Supporto SPA: se la rotta statica richiesta non esiste, ritorna index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path):
            self.path = '/index.html'
        return super().do_GET()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('', PORT), SPAHandler) as httpd:
    url = f"http://localhost:{PORT}"
    key = get_configured_api_key()
    print(f"🚀 Server Natalino avviato con successo su porta {PORT}!")
    if key:
        masked = key[:7] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"🔑 Chiave OpenAI caricata: {masked}")
    else:
        print(f"⚠️  Nessuna chiave OpenAI trovata.")
        print(f"   Puoi impostarla creando il file 'api_key.txt' o con 'export OPENAI_API_KEY=...'")
    print(f"🌐 Apri nel browser: {url}")
    print("Premi CTRL+C per terminare.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto del server in corso...")
