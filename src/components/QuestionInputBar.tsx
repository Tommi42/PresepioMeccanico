import React, { useState } from 'react';
import { Send } from 'lucide-react';

interface QuestionInputBarProps {
  currentQuestion: string;
  onAsk: (questionText: string) => void;
  disabled?: boolean;
}

export const QuestionInputBar: React.FC<QuestionInputBarProps> = ({
  currentQuestion,
  onAsk,
  disabled,
}) => {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || disabled) return;
    onAsk(inputText.trim());
    setInputText('');
  };

  return (
    <div className="w-full space-y-2">
      {/* Pinned Current Question (Kept at bottom as requested, clean and minimal) */}
      {currentQuestion && (
        <div className="px-4 py-2 rounded-xl bg-[#4a1715]/80 border border-amber-400/30 text-center animate-fade-in">
          <p className="text-xs text-amber-300 font-cartoon font-medium uppercase tracking-wider mb-0.5">
            Domanda:
          </p>
          <p className="text-sm sm:text-base font-cartoon font-semibold text-white truncate">
            «{currentQuestion}»
          </p>
        </div>
      )}

      {/* Child Keyboard Input Form */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={disabled}
          placeholder="Fai una domanda a Natalino con la tastiera..."
          className="flex-1 py-2.5 sm:py-3 px-4 rounded-2xl bg-[#fffdf7] text-[#2b1810] placeholder:text-stone-500 font-cartoon text-sm sm:text-base md:text-lg comic-border focus:outline-none focus:ring-2 focus:ring-amber-500 shadow-sm"
        />

        <button
          type="submit"
          disabled={!inputText.trim() || disabled}
          className="h-[46px] sm:h-[50px] px-5 sm:px-6 rounded-2xl bg-amber-600 hover:bg-amber-500 active:bg-amber-700 text-stone-950 font-cartoon font-bold text-sm sm:text-base flex items-center gap-1.5 border-2 border-amber-300/80 shadow-md active:scale-95 transition-all disabled:opacity-40 disabled:pointer-events-none cursor-pointer shrink-0"
        >
          <span>Chiedi</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
