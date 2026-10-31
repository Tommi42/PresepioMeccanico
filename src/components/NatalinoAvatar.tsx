import React, { useState, useEffect } from 'react';

interface NatalinoAvatarProps {
  status: 'idle' | 'thinking' | 'talking' | 'error';
  lastAskedAt?: number;
}

export const NatalinoAvatar: React.FC<NatalinoAvatarProps> = ({
  status,
  lastAskedAt,
}) => {
  const [isBowing, setIsBowing] = useState(false);

  // Trigger bow and hat lift whenever a new question is submitted / answered
  useEffect(() => {
    if (lastAskedAt) {
      triggerBow();
    }
  }, [lastAskedAt]);

  // Ambient periodic bow "una volta ogni tanto" (every 14 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      // Only do ambient bow if idle
      if (status === 'idle') {
        triggerBow();
      }
    }, 14000);

    return () => clearInterval(interval);
  }, [status]);

  const triggerBow = () => {
    if (isBowing) return;
    setIsBowing(true);
    // Return after 2.4s
    setTimeout(() => {
      setIsBowing(false);
    }, 2400);
  };

  return (
    <div
      onClick={triggerBow}
      title="Cliccami per farmi fare l'inchino!"
      className="relative flex flex-col items-center justify-end select-none shrink-0 cursor-pointer group"
    >
      {/* SVG Stylized Natalino matching the user's cartoon asset with smooth Hat & Bow animation */}
      <div className="relative w-28 sm:w-32 md:w-36 lg:w-36 h-auto">
        <svg
          viewBox="0 0 200 480"
          className="w-full h-auto overflow-visible relative z-10 transition-transform duration-300"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* WHOLE BODY (Head, Torso, Arms, Legs, Feet) */}
          <g
            id="natalinoBody"
            style={{
              transformOrigin: '95px 440px',
              transform: isBowing ? 'rotate(8deg) translateY(4px)' : 'rotate(0deg)',
              transition: 'transform 0.7s cubic-bezier(0.34, 1.3, 0.64, 1)',
            }}
          >
            {/* Feet (Rounded Peach Pills) */}
            <g id="feet">
              <rect x="46" y="420" width="46" height="42" rx="23" fill="#fed7c3" />
              <rect x="98" y="420" width="46" height="42" rx="23" fill="#fed7c3" />
            </g>

            {/* Legs (Straight Black Trousers with subtle center gap) */}
            <g id="legs">
              <rect x="46" y="275" width="46" height="150" fill="#000000" />
              <rect x="98" y="275" width="46" height="150" fill="#000000" />
            </g>

            {/* Torso & Jacket */}
            <g id="torso">
              {/* Main Black Jacket */}
              <rect x="42" y="145" width="106" height="135" rx="16" fill="#000000" />

              {/* Light Gray/White Collar/Lapel shape along the left side (back collar) */}
              <path
                d="M 104 145 C 132 145 146 160 146 185 L 146 220 C 138 215 130 180 104 145 Z"
                fill="#d9d9d9"
              />
            </g>

            {/* Arms extending forward/right */}
            <g id="arms">
              {/* Upper arm / sleeve */}
              <g
                style={{
                  transformOrigin: '140px 190px',
                  transform: isBowing ? 'rotate(-6deg)' : 'rotate(0deg)',
                  transition: 'transform 0.6s ease',
                }}
              >
                {/* Arm 1 (Background sleeve) */}
                <path
                  d="M 115 178 L 180 190 C 188 191 192 198 188 206 L 168 222 L 115 198 Z"
                  fill="#000000"
                />
                {/* Hand 1 */}
                <circle cx="198" cy="204" r="18" fill="#fed7c3" />

                {/* Arm 2 (Foreground sleeve) */}
                <path
                  d="M 110 205 L 158 245 C 166 251 166 260 158 268 L 138 280 L 105 235 Z"
                  fill="#000000"
                />
                {/* Hand 2 */}
                <circle cx="166" cy="268" r="18" fill="#fed7c3" />
              </g>
            </g>

            {/* Head (Stylized Peach Circle) */}
            <circle cx="95" cy="104" r="50" fill="#fed7c3" />
          </g>

          {/* TOP HAT (Independent layer that lifts up and tilts during bow!) */}
          <g
            id="natalinoTopHat"
            style={{
              transformOrigin: '95px 78px',
              transform: isBowing
                ? 'translateY(-46px) translateX(14px) rotate(-22deg)'
                : 'translateY(0px) translateX(0px) rotate(0deg)',
              transition: isBowing
                ? 'transform 0.7s cubic-bezier(0.2, 0.8, 0.2, 1)'
                : 'transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)',
            }}
          >
            {/* Hat Crown (Cylinder) */}
            <path
              d="M 66 12 C 64 8 126 8 124 12 L 128 72 L 62 72 Z"
              fill="#000000"
            />
            {/* Flat top oval */}
            <ellipse cx="95" cy="12" rx="29" ry="5" fill="#18181b" />

            {/* Red Ribbon Band */}
            <rect x="63" y="62" width="64" height="11" fill="#d00000" />

            {/* Wide Curved Hat Brim */}
            <ellipse cx="95" cy="74" rx="56" ry="16" fill="#000000" />
            <path
              d="M 39 74 Q 95 86 151 74 Q 95 62 39 74 Z"
              fill="#000000"
            />
          </g>
        </svg>
      </div>
    </div>
  );
};
