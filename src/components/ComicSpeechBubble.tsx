import React from 'react';

interface ComicSpeechBubbleProps {
  response: string;
  status: 'idle' | 'thinking' | 'talking' | 'error';
}

export const ComicSpeechBubble: React.FC<ComicSpeechBubbleProps> = ({
  response,
  status,
}) => {
  const isThinking = status === 'thinking';

  return (
    <div className="relative w-full max-w-xl lg:max-w-2xl select-none">
      {/* Comic Speech Bubble Box */}
      <div className="relative bg-[#fffef9] text-[#2b1810] rounded-[28px] p-6 sm:p-8 md:p-9 border-[3.5px] border-[#26150b] shadow-[0_14px_30px_rgba(0,0,0,0.45)]">
        
        {/* Seamless Comic Tail pointing to Natalino's head (higher up, at top: 38px) */}
        {/* Desktop / Landscape left-pointing tail */}
        <div className="hidden md:block">
          {/* Outer dark border triangle */}
          <div
            className="absolute top-9 -left-[23px] w-0 h-0"
            style={{
              borderTop: '15px solid transparent',
              borderBottom: '15px solid transparent',
              borderRight: '23px solid #26150b',
            }}
          />
          {/* Inner cream fill triangle seamlessly connecting to bubble interior */}
          <div
            className="absolute top-[38px] -left-[18px] w-0 h-0"
            style={{
              borderTop: '13px solid transparent',
              borderBottom: '13px solid transparent',
              borderRight: '20px solid #fffef9',
            }}
          />
        </div>

        {/* Mobile / Vertical layout: tail points downwards to Natalino below */}
        <div className="block md:hidden">
          <div
            className="absolute -bottom-[21px] left-12 w-0 h-0"
            style={{
              borderLeft: '15px solid transparent',
              borderRight: '15px solid transparent',
              borderTop: '21px solid #26150b',
            }}
          />
          <div
            className="absolute -bottom-[16px] left-[49px] w-0 h-0"
            style={{
              borderLeft: '14px solid transparent',
              borderRight: '14px solid transparent',
              borderTop: '18px solid #fffef9',
            }}
          />
        </div>

        {/* Bubble Text Content */}
        <div className="min-h-[85px] sm:min-h-[105px] flex items-center justify-center">
          {isThinking ? (
            <div className="flex items-center gap-3 py-2">
              <span className="text-lg sm:text-xl font-cartoon font-semibold text-amber-950 animate-pulse">
                Natalino sta pensando...
              </span>
              <div className="flex gap-1.5 items-center">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-700 animate-bounce [animation-delay:-0.3s]" />
                <span className="w-2.5 h-2.5 rounded-full bg-amber-700 animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2.5 h-2.5 rounded-full bg-amber-700 animate-bounce" />
              </div>
            </div>
          ) : (
            <p className="text-lg sm:text-xl md:text-[22px] leading-relaxed text-[#26150b] font-cartoon font-medium text-left">
              «{response}»
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
