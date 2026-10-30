/**
 * Types for Natalino's Interactive Nativity Screen
 */

export interface AppConfig {
  openaiApiKey: string;
  selectedModel: string;
  systemPrompt: string;
  temperature: number;
}

export interface QuickQuestion {
  id: string;
  label: string;
  fullQuestion: string;
  iconName: 'user' | 'cog' | 'sparkles' | 'tree' | 'smile' | 'water' | 'heart';
  fallbackAnswer: string;
}

export interface NatalinoState {
  currentQuestion: string;
  response: string;
  status: 'idle' | 'thinking' | 'talking' | 'error';
  lastAskedAt?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
