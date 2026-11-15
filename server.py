import csv
import datetime
import http.server
import io
import json
import os
import socketserver
import sys
import threading
import uuid
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTORY = os.path.join(BASE_DIR, 'dist')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOGS_DIR, 'conversations.jsonl')

os.makedirs(LOGS_DIR, exist_ok=True)
log_lock = threading.Lock()

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
    key_file = os.path.join(BASE_DIR, 'api_key.txt')
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
        os.path.join(BASE_DIR, 'config.json'),
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


def append_conversation_log(entry: dict) -> dict:
    now = datetime.datetime.now()
    if 'id' not in entry or not entry['id']:
        entry['id'] = f"log_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    if 'datetime_local' not in entry or not entry['datetime_local']:
        entry['datetime_local'] = now.strftime('%Y-%m-%d %H:%M:%S')
    if 'timestamp' not in entry or not entry['timestamp']:
        entry['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    line = json.dumps(entry, ensure_ascii=False) + '\n'
    with log_lock:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    return entry


def read_conversation_logs(limit=None, search=None, source_filter=None, date_filter=None):
    if not os.path.exists(LOG_FILE):
        return []

    records = []
    with log_lock:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Errore nella lettura dei log: {e}")
            return []

    # Ordine cronologico decrescente (i più recenti per primi)
    records.reverse()

    if search:
        s_lower = search.lower().strip()
        records = [
            r for r in records
            if s_lower in r.get('question', '').lower() or s_lower in r.get('answer', '').lower()
        ]

    if source_filter:
        sf = source_filter.lower().strip()
        if sf == 'openai':
            records = [r for r in records if r.get('isFromOpenAi') is True]
        elif sf in ('fallback', 'offline'):
            records = [r for r in records if r.get('isFromOpenAi') is False and not r.get('errorNote')]
        elif sf == 'error':
            records = [r for r in records if bool(r.get('errorNote'))]

    if date_filter:
        df = date_filter.strip()
        records = [
            r for r in records
            if df in (r.get('datetime_local') or r.get('timestamp') or '')
        ]

    if limit and isinstance(limit, int) and limit > 0:
        records = records[:limit]

    return records


def compute_log_stats():
    if not os.path.exists(LOG_FILE):
        return {
            'total': 0,
            'today': 0,
            'openaiCount': 0,
            'fallbackCount': 0,
            'errorCount': 0,
            'avgDurationMs': 0
        }

    total = 0
    today_count = 0
    openai_count = 0
    fallback_count = 0
    error_count = 0
    durations = []

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')

    with log_lock:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        total += 1
                        ts = r.get('datetime_local') or r.get('timestamp') or ''
                        if today_str in ts:
                            today_count += 1
                        if r.get('isFromOpenAi'):
                            openai_count += 1
                        else:
                            fallback_count += 1
                        if r.get('errorNote'):
                            error_count += 1
                        d = r.get('durationMs')
                        if isinstance(d, (int, float)) and d > 0:
                            durations.append(d)
                    except Exception:
                        continue
        except Exception:
            pass

    avg_dur = round(sum(durations) / len(durations)) if durations else 0
    return {
        'total': total,
        'today': today_count,
        'openaiCount': openai_count,
        'fallbackCount': fallback_count,
        'errorCount': error_count,
        'avgDurationMs': avg_dur
    }


def generate_csv_bytes(records):
    output = io.StringIO()
    # Scrittura del BOM UTF-8 affinché Excel apra correttamente i caratteri accentati
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        'ID',
        'Data e Ora',
        'Domanda',
        'Risposta',
        'Origine',
        'Modello',
        'Durata (ms)',
        'Errori / Note'
    ])
    for r in records:
        orig = 'OpenAI' if r.get('isFromOpenAi') else 'Riserva Locale'
        q = (r.get('question') or '').replace('\r\n', ' ').replace('\n', ' ')
        a = (r.get('answer') or '').replace('\r\n', ' ').replace('\n', ' ')
        writer.writerow([
            r.get('id', ''),
            r.get('datetime_local', '') or r.get('timestamp', ''),
            q,
            a,
            orig,
            r.get('model', ''),
            r.get('durationMs', ''),
            r.get('errorNote', '') or ''
        ])
    return output.getvalue().encode('utf-8')


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Natalino — Registro Conversazioni Presepio</title>
  <style>
    :root {
      --bg-page: #fbf8f5;
      --card-bg: #ffffff;
      --primary: #9e3b37;
      --primary-dark: #7a2622;
      --accent: #d97706;
      --text: #26150b;
      --text-muted: #786b62;
      --border: #eadfce;
      --openai-bg: #ecfdf5;
      --openai-text: #047857;
      --fallback-bg: #fffbeb;
      --fallback-text: #b45309;
      --error-bg: #fef2f2;
      --error-text: #b91c1c;
      --radius: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-page);
      color: var(--text);
      line-height: 1.5;
      padding-bottom: 60px;
    }
    header {
      background: linear-gradient(135deg, #7d2927 0%, #a23f3b 50%, #631f1d 100%);
      color: #fff;
      padding: 24px 20px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    .container {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 16px;
    }
    .header-top {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .header-title h1 {
      font-size: 1.65rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .header-title p {
      color: #fde68a;
      font-size: 0.9rem;
      margin-top: 4px;
    }
    .header-actions {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 9px 16px;
      border-radius: 9px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease-in-out;
      border: 1px solid transparent;
    }
    .btn-gold {
      background: #fef3c7;
      color: #78350f;
      border-color: #fde68a;
    }
    .btn-gold:hover { background: #fde68a; }
    .btn-white {
      background: rgba(255,255,255,0.15);
      color: #ffffff;
      border-color: rgba(255,255,255,0.3);
    }
    .btn-white:hover { background: rgba(255,255,255,0.25); }
    .btn-primary {
      background: var(--primary);
      color: #fff;
    }
    .btn-primary:hover { background: var(--primary-dark); }
    
    /* KPI Stats */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
      margin-top: -20px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 18px 20px;
      border: 1px solid var(--border);
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .stat-label {
      font-size: 0.8rem;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--text-muted);
      letter-spacing: 0.5px;
    }
    .stat-value {
      font-size: 1.85rem;
      font-weight: 700;
      color: var(--text);
      margin-top: 4px;
    }
    .stat-sub {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Filters toolbar */
    .toolbar {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 14px 18px;
      border: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 20px;
    }
    .search-input {
      flex: 1;
      min-width: 220px;
      padding: 9px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      font-size: 0.92rem;
      background: #faf7f2;
      outline: none;
    }
    .search-input:focus {
      border-color: var(--accent);
      background: #ffffff;
    }
    .select-filter {
      padding: 9px 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      font-size: 0.88rem;
      background: #faf7f2;
      cursor: pointer;
    }
    .live-toggle {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.84rem;
      color: var(--text-muted);
      cursor: pointer;
      user-select: none;
    }
    .live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      display: inline-block;
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0% { opacity: 0.5; }
      50% { opacity: 1; transform: scale(1.15); }
      100% { opacity: 0.5; }
    }

    /* Logs feed */
    .log-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .log-item {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 20px;
      border: 1px solid var(--border);
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
      transition: transform 0.1s ease;
    }
    .log-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid #f3ede2;
    }
    .log-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .log-time {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .badge {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .badge-openai { background: var(--openai-bg); color: var(--openai-text); }
    .badge-fallback { background: var(--fallback-bg); color: var(--fallback-text); }
    .badge-error { background: var(--error-bg); color: var(--error-text); }
    .badge-time { background: #f3f4f6; color: #4b5563; font-weight: 500; }

    .log-question {
      font-size: 1.05rem;
      font-weight: 700;
      color: #7a2622;
      margin-bottom: 10px;
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }
    .log-question-mark {
      color: var(--accent);
      font-size: 1.2rem;
      line-height: 1;
    }
    .log-answer {
      font-size: 0.95rem;
      color: #382923;
      background: #faf7f2;
      border-left: 3px solid #d4c5b3;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      line-height: 1.55;
    }
    .log-error-box {
      margin-top: 10px;
      font-size: 0.82rem;
      background: var(--error-bg);
      color: var(--error-text);
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid #fecaca;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      background: var(--card-bg);
      border-radius: var(--radius);
      border: 1px dashed var(--border);
      color: var(--text-muted);
    }
    .empty-state h3 {
      font-size: 1.2rem;
      color: var(--text);
      margin-bottom: 6px;
    }
  </style>
</head>
<body>

  <header>
    <div class="container header-top">
      <div class="header-title">
        <h1>🌟 Natalino — Registro Conversazioni</h1>
        <p>Presepio Meccanico della SS. Annunziata di Torino</p>
      </div>
      <div class="header-actions">
        <a href="/api/logs/export.csv" class="btn btn-gold" download title="Esporta tutte le conversazioni in formato CSV per Excel">
          📥 Esporta CSV / Excel
        </a>
        <button id="refreshBtn" class="btn btn-white" onclick="loadLogs()">
          🔄 Aggiorna
        </button>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Statistiche KPI -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Domande Totali</div>
        <div class="stat-value" id="statTotal">-</div>
        <div class="stat-sub">Registrate nel presepio</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Domande Oggi</div>
        <div class="stat-value" id="statToday" style="color: #9e3b37;">-</div>
        <div class="stat-sub">Sessione odierna</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Risposte con OpenAI</div>
        <div class="stat-value" id="statOpenAi" style="color: #047857;">-</div>
        <div class="stat-sub" id="statOpenAiPct">0% del totale</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Riserva / Offline</div>
        <div class="stat-value" id="statFallback" style="color: #b45309;">-</div>
        <div class="stat-sub" id="statFallbackPct">0% del totale</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Tempo Medio Risposta</div>
        <div class="stat-value" id="statDuration">-</div>
        <div class="stat-sub">Latenza media AI</div>
      </div>
    </div>

    <!-- Barra di ricerca e filtri -->
    <div class="toolbar">
      <input
        type="text"
        id="searchInput"
        class="search-input"
        placeholder="🔍 Cerca nelle domande o risposte (es. 'mucca', 'motore', 'legno')..."
        oninput="applyFilter()"
      >
      <select id="sourceFilter" class="select-filter" onchange="applyFilter()">
        <option value="all">Tutte le origini</option>
        <option value="openai">Solo OpenAI</option>
        <option value="fallback">Solo Riserva Locale</option>
        <option value="error">Solo con Errori</option>
      </select>
      <select id="dateFilter" class="select-filter" onchange="applyFilter()">
        <option value="all">Tutte le date</option>
        <option value="today">Solo Oggi</option>
      </select>
      <label class="live-toggle">
        <input type="checkbox" id="liveToggle" checked onchange="toggleLiveRefresh(this.checked)">
        <span class="live-dot"></span> Live (5s)
      </label>
    </div>

    <!-- Elenco conversazioni -->
    <div id="logContainer" class="log-list">
      <div class="empty-state">
        <h3>Caricamento delle conversazioni...</h3>
      </div>
    </div>
  </main>

  <script>
    let rawLogs = [];
    let liveTimer = null;

    async function loadLogs() {
      try {
        const res = await fetch('/api/logs?limit=500&t=' + Date.now());
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        
        rawLogs = data.logs || [];
        updateStats(data.stats || {});
        applyFilter();
      } catch (err) {
        console.error('Errore caricamento log:', err);
      }
    }

    function updateStats(stats) {
      document.getElementById('statTotal').innerText = stats.total || 0;
      document.getElementById('statToday').innerText = stats.today || 0;
      document.getElementById('statOpenAi').innerText = stats.openaiCount || 0;
      document.getElementById('statFallback').innerText = stats.fallbackCount || 0;

      const total = stats.total || 1;
      const oPct = Math.round(((stats.openaiCount || 0) / total) * 100);
      const fPct = Math.round(((stats.fallbackCount || 0) / total) * 100);
      document.getElementById('statOpenAiPct').innerText = oPct + '% del totale';
      document.getElementById('statFallbackPct').innerText = fPct + '% del totale';

      const durSec = (stats.avgDurationMs ? (stats.avgDurationMs / 1000).toFixed(1) : 0) + 's';
      document.getElementById('statDuration').innerText = durSec;
    }

    function applyFilter() {
      const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      const src = document.getElementById('sourceFilter').value;
      const dt = document.getElementById('dateFilter').value;
      const todayStr = new Date().toISOString().slice(0, 10);

      const filtered = rawLogs.filter(item => {
        if (q) {
          const matchQ = (item.question || '').toLowerCase().includes(q);
          const matchA = (item.answer || '').toLowerCase().includes(q);
          if (!matchQ && !matchA) return false;
        }

        if (src === 'openai' && !item.isFromOpenAi) return false;
        if (src === 'fallback' && (item.isFromOpenAi || item.errorNote)) return false;
        if (src === 'error' && !item.errorNote) return false;

        if (dt === 'today') {
          const itemDt = item.datetime_local || item.timestamp || '';
          if (!itemDt.includes(todayStr)) return false;
        }

        return true;
      });

      renderLogs(filtered);
    }

    function renderLogs(logs) {
      const container = document.getElementById('logContainer');
      if (!logs || logs.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <h3>Nessuna conversazione trovata</h3>
            <p>Le domande rivolte a Natalino al presepio compariranno automaticamente qui in tempo reale.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = logs.map(item => {
        const isAi = !!item.isFromOpenAi;
        const dur = item.durationMs ? (item.durationMs / 1000).toFixed(1) + 's' : null;
        const timeStr = item.datetime_local || new Date(item.timestamp).toLocaleString('it-IT');

        let badge = '';
        if (item.errorNote) {
          badge = `<span class="badge badge-error">⚠️ Fallback Errore</span>`;
        } else if (isAi) {
          badge = `<span class="badge badge-openai">🤖 OpenAI (${escapeHtml(item.model || 'gpt-4o-mini')})</span>`;
        } else {
          badge = `<span class="badge badge-fallback">💾 Riserva Locale</span>`;
        }

        const durBadge = dur ? `<span class="badge badge-time">⏱️ ${dur}</span>` : '';
        const errorBox = item.errorNote ? `
          <div class="log-error-box">
            <strong>Nota di sistema:</strong> ${escapeHtml(item.errorNote)}
          </div>
        ` : '';

        return `
          <div class="log-item">
            <div class="log-header">
              <div class="log-meta">
                <span class="log-time">🕒 ${escapeHtml(timeStr)}</span>
                ${badge}
                ${durBadge}
              </div>
            </div>
            <div class="log-question">
              <span class="log-question-mark">❓</span>
              <span>« ${escapeHtml(item.question || '')} »</span>
            </div>
            <div class="log-answer">
              ${escapeHtml(item.answer || '')}
            </div>
            ${errorBox}
          </div>
        `;
      }).join('');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function toggleLiveRefresh(enabled) {
      if (liveTimer) clearInterval(liveTimer);
      if (enabled) {
        liveTimer = setInterval(loadLogs, 5000);
      }
    }

    // Avvio automatico al caricamento della pagina
    loadLogs();
    toggleLiveRefresh(true);
  </script>
</body>
</html>
"""


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        # Supporto CORS preflight
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. Endpoint configurazione OpenAI a runtime
        if clean_path in ('/api/config', '/config.json'):
            api_key = get_configured_api_key()
            response_data = json.dumps({'openaiApiKey': api_key}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(response_data)
            return

        # 2. Endpoint lettura log conversazioni (/api/logs)
        if clean_path == '/api/logs':
            limit_val = query_params.get('limit', ['100'])[0]
            limit = None if limit_val == 'all' else int(limit_val) if limit_val.isdigit() else 100
            search = query_params.get('search', [None])[0]
            source = query_params.get('source', [None])[0]
            date_f = query_params.get('date', [None])[0]

            logs = read_conversation_logs(limit=limit, search=search, source_filter=source, date_filter=date_f)
            stats = compute_log_stats()

            res_payload = {
                'status': 'ok',
                'count': len(logs),
                'stats': stats,
                'logs': logs
            }
            res_bytes = json.dumps(res_payload, ensure_ascii=False).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(res_bytes)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(res_bytes)
            return

        # 3. Endpoint esportazione CSV per Excel (/api/logs/export.csv)
        if clean_path in ('/api/logs/export.csv', '/api/logs.csv'):
            logs = read_conversation_logs(limit=None)
            csv_bytes = generate_csv_bytes(logs)
            filename = f"conversazioni_natalino_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(csv_bytes)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        # 4. Web Dashboard per visualizzare i log (/logs o /admin/logs)
        if clean_path in ('/logs', '/logs/', '/admin/logs', '/logs.html'):
            html_bytes = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_bytes)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        # 5. Supporto SPA: se la risorsa statica richiesta non esiste, ritorna index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path):
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        clean_path = self.path.split('?')[0]

        # Endpoint registrazione log conversazione (/api/logs)
        if clean_path == '/api/logs':
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len) if content_len > 0 else b'{}'
                entry = json.loads(body.decode('utf-8'))
                
                saved = append_conversation_log(entry)
                res_bytes = json.dumps({'status': 'ok', 'id': saved.get('id')}).encode('utf-8')

                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(res_bytes)))
                self.end_headers()
                self.wfile.write(res_bytes)
                return
            except Exception as e:
                err_bytes = json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8')
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(err_bytes)))
                self.end_headers()
                self.wfile.write(err_bytes)
                return

        self.send_response(404)
        self.end_headers()


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('', PORT), SPAHandler) as httpd:
    url = f"http://localhost:{PORT}"
    logs_url = f"http://localhost:{PORT}/logs"
    key = get_configured_api_key()
    print(f"🚀 Server Natalino avviato con successo su porta {PORT}!")
    if key:
        masked = key[:7] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"🔑 Chiave OpenAI caricata: {masked}")
    else:
        print(f"⚠️  Nessuna chiave OpenAI trovata.")
        print(f"   Puoi impostarla creando il file 'api_key.txt' o con 'export OPENAI_API_KEY=...'")
    print(f"🌐 Interfaccia Kiosk Natalino: {url}")
    print(f"📊 Dashboard Visualizzazione Log: {logs_url}")
    print(f"📁 File di archivio conversazioni: {LOG_FILE}")
    print("Premi CTRL+C per terminare.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto del server in corso...")
