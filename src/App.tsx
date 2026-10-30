import { useState } from 'react';
import { AppConfig, NatalinoState, QuickQuestion } from './types';
import { getStoredConfig, saveConfig, askNatalino } from './services/aiService';
import { NatalinoAvatar } from './components/NatalinoAvatar';
import { ComicSpeechBubble } from './components/ComicSpeechBubble';
import { QuickQuestionsBar } from './components/QuickQuestionsBar';
import { QuestionInputBar } from './components/QuestionInputBar';

const INITIAL_GREETING =
  'Ciao! Sono Natalino. Chiedimi pure qualsiasi curiosità sul nostro presepio!';

export default function App() {
  const [config] = useState<AppConfig>(getStoredConfig);

  const [state, setState] = useState<NatalinoState>({
    currentQuestion: '',
    response: INITIAL_GREETING,
    status: 'idle',
    lastAskedAt: undefined,
  });

  const handleAsk = async (questionText: string) => {
    if (!questionText.trim()) return;

    setState((prev) => ({
      ...prev,
      currentQuestion: questionText,
      status: 'thinking',
    }));

    try {
      const result = await askNatalino(questionText, config);

      setState((prev) => ({
        ...prev,
        response: result.text,
        status: 'talking',
        lastAskedAt: Date.now(),
      }));

      setTimeout(() => {
        setState((prev) => (prev.status === 'talking' ? { ...prev, status: 'idle' } : prev));
      }, 5000);
    } catch (e: unknown) {
      console.error(e);
      setState((prev) => ({
        ...prev,
        status: 'error',
        response:
          'Ho avuto un piccolo intoppo coi miei ingranaggi! Riprova tra poco.',
      }));
    }
  };

  const handleQuickQuestion = (question: QuickQuestion) => {
    handleAsk(question.fullQuestion);
  };

  return (
    <div className="h-screen w-screen max-h-screen overflow-hidden flex flex-col justify-between bg-[#26150b] text-amber-50 select-none relative p-3 sm:p-5">
      {/* Warm rustic wood backdrop */}
      <div
        className="fixed inset-0 pointer-events-none opacity-45 mix-blend-overlay"
        style={{
          backgroundImage: `
            repeating-linear-gradient(0deg, #3d2113 0px, #2b160b 80px, #3d2113 160px)
          `,
        }}
      />

      {/* Top minimal title: ONLY "Natalino", centered and clean */}
      <header className="relative z-10 text-center pt-1 pb-1 shrink-0">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-cartoon font-bold text-amber-100 tracking-wide drop-shadow-md">
          Natalino
        </h1>
      </header>

      {/* Center stage: Stylized Animated Natalino on left + Speech Bubble on right with ample gap */}
      <main className="relative z-10 flex-1 flex flex-col md:flex-row items-center justify-center gap-6 sm:gap-10 md:gap-14 px-4 sm:px-8 min-h-0">
        
        {/* Natalino Avatar (with Bowing & Hat-tipping animation) */}
        <div className="order-2 md:order-1 flex justify-center shrink-0">
          <NatalinoAvatar
            status={state.status}
            lastAskedAt={state.lastAskedAt}
          />
        </div>

        {/* Comic Speech Bubble (Pointer aligned near head, zero overlap) */}
        <div className="order-1 md:order-2 flex justify-center w-full max-w-xl md:max-w-2xl shrink-0">
          <ComicSpeechBubble
            response={state.response}
            status={state.status}
          />
        </div>
      </main>

      {/* Bottom Area: Quick Suggestions + Current Question + Keyboard Input */}
      <footer className="relative z-10 shrink-0 w-full max-w-3xl mx-auto space-y-2 pb-1">
        {/* Quick Question Buttons */}
        <QuickQuestionsBar
          onSelectQuestion={handleQuickQuestion}
          disabled={state.status === 'thinking'}
        />

        {/* Pinned Current Question & Large Input Form */}
        <QuestionInputBar
          currentQuestion={state.currentQuestion}
          onAsk={handleAsk}
          disabled={state.status === 'thinking'}
        />
      </footer>
    </div>
  );
}
