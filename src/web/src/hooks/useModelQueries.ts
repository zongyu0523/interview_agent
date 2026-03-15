import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./queryKeys";

const MODEL_STORAGE_KEY = "jiaf_model_settings";

const DEFAULT_MODELS: Record<string, string> = {
  chat_agent:     "anthropic/claude-sonnet-4-6",
  task_generator: "anthropic/claude-sonnet-4-6",
  resume_parser:  "anthropic/claude-sonnet-4-6",
  scorer:         "anthropic/claude-haiku-4-5-20251001",
  match_analyzer: "anthropic/claude-haiku-4-5-20251001",
  tts:            "openai/tts-1",
  stt:            "openai/whisper-1",
};

function loadModels(): Record<string, string> {
  try {
    const stored = localStorage.getItem(MODEL_STORAGE_KEY);
    return stored ? { ...DEFAULT_MODELS, ...JSON.parse(stored) } : { ...DEFAULT_MODELS };
  } catch {
    return { ...DEFAULT_MODELS };
  }
}

export function getStoredModels(): Record<string, string> {
  return loadModels();
}

export function useModels() {
  return useQuery({
    queryKey: queryKeys.models.all(),
    queryFn: loadModels,
    staleTime: Infinity,
  });
}

export function useUpdateModels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (models: Record<string, string>) => {
      localStorage.setItem(MODEL_STORAGE_KEY, JSON.stringify(models));
      return models;
    },
    onSuccess: (newModels) => {
      queryClient.setQueryData(queryKeys.models.all(), newModels);
    },
  });
}
