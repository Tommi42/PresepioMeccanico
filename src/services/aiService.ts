import { AppConfig } from '../types';
import { DEFAULT_CONFIG, DEFAULT_QUICK_QUESTIONS, OPENAI_API_KEY, OPENAI_MODEL } from '../data/defaultConfig';

const STORAGE_KEY = 'natalino_presepio_config_v1';

export function getStoredConfig(): AppConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        ...DEFAULT_CONFIG,
        ...parsed,
        openaiApiKey: OPENAI_API_KEY || parsed.openaiApiKey || '',
        selectedModel: OPENAI_MODEL || parsed.selectedModel || 'gpt-4o-mini',
      };
    }
  } catch (e) {
    console.warn('Could not read config from localStorage', e);
  }
  return DEFAULT_CONFIG;
}

export function saveConfig(config: AppConfig): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  } catch (e) {
    console.error('Failed to save config to localStorage', e);
  }
}

/**
 * Intelligent local fallback based on keywords if OpenAI key is not entered yet or offline
 */
function getLocalFallbackAnswer(question: string): string {
  const q = question.toLowerCase();

  // Match predefined questions
  for (const item of DEFAULT_QUICK_QUESTIONS) {
    if (q.includes(item.id) || q.includes(item.label.toLowerCase())) {
      return item.fallbackAnswer;
    }
  }

  if (q.includes('chi sei') || q.includes('tuo nome') || q.includes('cappello') || q.includes('cilindro') || q.includes('vestito') || q.includes('frac')) {
    return 'Sono Natalino, il robottino custode in frac e cilindro! Sono stato costruito nel 2011 da una preziosa statuetta in legno di cirmolo trovata nei sotterranei, e quando i visitatori toccano la mia pedana mi tolgo il cappello per fare un reverente inchino di benvenuto!';
  }

  if (q.includes('motore') || q.includes('nave') || q.includes('moviment') || q.includes('cinghie') || q.includes('pulegg')) {
    return 'Pensa che meraviglia: tutto questo presepio è mosso da un unico antico motore elettrico dell’Ottocento, recuperato da una nave in demolizione! Con oltre cento pulegge e cinghie speciali, trasmette il movimento a più di cento personaggi contemporaneamente!';
  }

  if (q.includes('mucca') || q.includes('visone') || q.includes('nestl') || q.includes('animale')) {
    return 'Muuu! La nostra simpatica mucca vicino alla grotta ha un meccanismo svizzero che le fa muovere testa, coda, occhi e voce! Il volontario Fiorenzo Fassino le ha perfino cucito un morbido cappottino in finto visone per tenerla al caldo!';
  }

  if (q.includes('legno') || q.includes('statue') || q.includes('cirmolo') || q.includes('ortisei') || q.includes('val gardena')) {
    return 'Le nostre oltre duecento statue sono veri tesori d’arte! Moltissime sono state scolpite a mano nel profumato legno di cirmolo (il pino cembro delle montagne della Val Gardena), un legno così dolce e resistente che non viene intaccato dai tarli nemmeno dopo un secolo!';
  }

  if (q.includes('acqua') || q.includes('fiume') || q.includes('lago') || q.includes('ruscell') || q.includes('pescatore')) {
    return 'L’acqua che vedi scorrere è freschissima e vera! Sotto il pavimento c’è un impianto idraulico con ottanta litri d’acqua che salgono alle cascatelle e scendono nei fiumi, dove le lavandaie fanno il bucato e le barchette galleggiano tranquille!';
  }

  if (q.includes('volontar') || q.includes('chi ha fatto') || q.includes('inventato') || q.includes('canonica') || q.includes('beppe')) {
    return 'Il presepio è nato oltre cent’anni fa (nel 1909-1910) grazie alla fantasia di Francesco Canonica e di suo figlio Maggiorino, un regista del cinema! Oggi se ne prendono cura quaranta volontari con il presepio nel cuore: riparano gli ingranaggi, cuciono i vestiti e accolgono tutti col sorriso!';
  }

  if (q.includes('bambin') || q.includes('ges') || q.includes('natale') || q.includes('grotta') || q.includes('stella')) {
    return 'Il cuore di tutto il presepio è la Grotta Santa di Betlemme! Lì c’è Gesù Bambino che accoglie i pastori, illuminato da una stella cometa color ambra e dal grande amore di Maria e Giuseppe. È la festa più bella dell’anno!';
  }

  return 'Che bella domanda! Nel nostro grande presepio della SS. Annunziata ci sono oltre duecento statue, fiumi con acqua vera e un motore di nave dell’Ottocento che fa muovere tutto! Vieni a scoprire le mie storie: chiedimi del mio vestito, della mucca con la pelliccia o del segreto delle nostre statue di legno!';
}

export async function askNatalino(
  question: string,
  config: AppConfig
): Promise<{ text: string; isFromOpenAi: boolean; errorNote?: string }> {
  // If OpenAI API key is provided, attempt connection
  const apiKey = (config.openaiApiKey || '').trim();

  if (!apiKey) {
    // Return friendly local answer immediately
    return {
      text: getLocalFallbackAnswer(question),
      isFromOpenAi: false,
    };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 18000);

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: config.selectedModel || 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: config.systemPrompt || DEFAULT_CONFIG.systemPrompt,
          },
          {
            role: 'user',
            content: question,
          },
        ],
        temperature: config.temperature ?? 0.7,
        max_tokens: 350,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData?.error?.message || `HTTP error ${response.status}`;
      console.warn('OpenAI error:', errorMsg);

      return {
        text: getLocalFallbackAnswer(question),
        isFromOpenAi: false,
        errorNote: `OpenAI: ${errorMsg}. Risposta fornita dalla memoria di riserva di Natalino.`,
      };
    }

    const data = await response.json();
    const reply = data.choices?.[0]?.message?.content?.trim();

    if (reply) {
      return {
        text: reply,
        isFromOpenAi: true,
      };
    }

    return {
      text: getLocalFallbackAnswer(question),
      isFromOpenAi: false,
      errorNote: 'Risposta vuota da OpenAI, usato fallback locale.',
    };
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : String(err);
    console.warn('Fetch error:', errMessage);
    return {
      text: getLocalFallbackAnswer(question),
      isFromOpenAi: false,
      errorNote: `Connessione non riuscita (${errMessage}). Risposta fornita dalla memoria interna di Natalino.`,
    };
  }
}

export async function testOpenAiConnection(
  apiKey: string,
  model: string
): Promise<{ success: boolean; message: string }> {
  if (!apiKey.trim()) {
    return {
      success: false,
      message: 'Inserisci una chiave API prima di testare.',
    };
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey.trim()}`,
      },
      body: JSON.stringify({
        model: model || 'gpt-4o-mini',
        messages: [
          { role: 'system', content: 'Rispondi brevemente con un saluto festoso da Natalino.' },
          { role: 'user', content: 'Ciao!' },
        ],
        max_tokens: 50,
      }),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      return {
        success: false,
        message: errJson?.error?.message || `Errore HTTP ${response.status}`,
      };
    }

    const data = await response.json();
    const reply = data.choices?.[0]?.message?.content;
    return {
      success: true,
      message: `Connessione riuscita! Risposta test: "${reply || 'OK'}"`,
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      success: false,
      message: `Errore di rete: ${msg}`,
    };
  }
}
