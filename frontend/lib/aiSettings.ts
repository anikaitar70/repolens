export type AiProvider = "groq" | "openai" | "gemini" | "anthropic" | "openrouter";

export interface AiSettings {
  provider: AiProvider;
  model: string;
  apiKey: string;
}

const STORAGE_KEY = "repolens_ai_settings";

export const DEFAULT_MODELS: Record<AiProvider, string> = {
  groq: "llama-3.3-70b-versatile",
  openai: "gpt-4o-mini",
  gemini: "gemini-2.0-flash",
  anthropic: "claude-3-5-sonnet-20241022",
  openrouter: "llama-3.3-70b-versatile",
};

export const PROVIDER_LABELS: Record<AiProvider, string> = {
  groq: "Groq",
  openai: "OpenAI",
  gemini: "Gemini",
  anthropic: "Anthropic",
  openrouter: "OpenRouter",
};

export const DEFAULT_AI_SETTINGS: AiSettings = {
  provider: "groq",
  model: DEFAULT_MODELS.groq,
  apiKey: "",
};

export function loadAiSettings(): AiSettings {
  if (typeof window === "undefined") {
    return DEFAULT_AI_SETTINGS;
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return DEFAULT_AI_SETTINGS;
    }
    const parsed = JSON.parse(raw) as Partial<AiSettings>;
    const provider = (parsed.provider ?? "groq") as AiProvider;
    return {
      provider,
      model: parsed.model ?? DEFAULT_MODELS[provider],
      apiKey: parsed.apiKey ?? "",
    };
  } catch {
    return DEFAULT_AI_SETTINGS;
  }
}

export function saveAiSettings(settings: AiSettings): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function hasAiKey(settings: AiSettings): boolean {
  return settings.apiKey.trim().length > 0;
}
