import React from 'react';
import { QuickQuestion } from '../types';
import { DEFAULT_QUICK_QUESTIONS } from '../data/defaultConfig';

interface QuickQuestionsBarProps {
  onSelectQuestion: (question: QuickQuestion) => void;
  disabled?: boolean;
}

export const QuickQuestionsBar: React.FC<QuickQuestionsBarProps> = ({
  onSelectQuestion,
  disabled,
}) => {
  return (
    <div className="w-full">
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
        {DEFAULT_QUICK_QUESTIONS.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectQuestion(item)}
            disabled={disabled}
            className="px-3 py-1.5 rounded-xl bg-[#4d1917]/80 hover:bg-[#64211e] active:bg-[#381110] text-amber-100 hover:text-white border border-amber-400/30 shadow-sm text-xs sm:text-sm font-cartoon font-medium transition-all active:scale-95 disabled:opacity-40 disabled:pointer-events-none cursor-pointer whitespace-nowrap"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
