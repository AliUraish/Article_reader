
export enum ModelType {
  GPT = 'gpt',
  GEMINI = 'gemini'
}

export enum SummaryFormat {
  BULLET_POINTS = 'BULLET_POINTS',
  PARAGRAPH = 'PARAGRAPH'
}

export interface SummaryRecord {
  id: string;
  url: string;
  title: string;
  content: string;
  summary: string;
  format: SummaryFormat;
  maxWords: number;
  model: ModelType;
  timestamp: number;
}

export interface AppState {
  url: string;
  format: SummaryFormat;
  maxWords: number;
  selectedModel: ModelType;
  isLoading: boolean;
  error: string | null;
  history: SummaryRecord[];
  currentSummary: SummaryRecord | null;
}
