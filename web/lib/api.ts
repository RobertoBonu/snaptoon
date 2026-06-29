/**
 * Helper API client tipizzato per il frontend.
 *
 * In futuro (sett. 6 polish) si genererà automaticamente da OpenAPI schema
 * di FastAPI con openapi-typescript. Per ora: tipi definiti a mano per i
 * payload effettivamente usati.
 */

export interface User {
  id: string;
  email: string;
  role: string;
  is_admin: boolean;
  must_change_password: boolean;
}

export interface Project {
  id: string;
  slug: string;
  title: string;
  length_target: string;
  style_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectList {
  projects: Project[];
  max_projects: number;
  current_count: number;
}

export interface Account {
  id: string;
  email: string;
  role: string;
  is_admin: boolean;
  plan: string;
  plan_label: string;
  credits_used: number;
  credits_total: number;
  credits_remaining: number;
  max_projects: number;
  created_at: string;
  must_change_password: boolean;
}

export interface CreditEntry {
  operation: string;
  delta: number;
  reason?: string | null;
  reference_id?: string | null;
  occurred_at: string;
}

export interface CreditHistory {
  entries: CreditEntry[];
}

// === KIDS ===

export interface KidsTemplate {
  id: string;
  slug: string;
  label: string;
  n_characters: number;
  length_target: string;
  grid_distribution: string[];
  scene_distribution: Array<Record<string, unknown>>;
  notes: string;
}

export interface KidsStyle {
  slug: string;
  label: string;
  preset_id: string;
}

export interface KidsProject {
  id: string;
  slug: string;
  name: string;
  style_id?: string | null;
  style_label?: string | null;
  created_at: string;
  updated_at: string;
}

export interface KidsCharacterIn {
  name: string;
  description: string;
}

export interface KidsProjectCreateIn {
  template_id: string;
  style_slug: string;
  scintilla: string;
  characters: KidsCharacterIn[];
}

export interface KidsPanel {
  number: number;
  description: string;
  dialogue_speaker?: string | null;
  dialogue_text?: string | null;
}

export interface KidsPage {
  number: number;
  panels: KidsPanel[];
}

export interface KidsStory {
  logline: string;
  pages: KidsPage[];
}

export interface KidsVignetteStatus {
  page_number: number;
  panel_number: number;
  generated: boolean;
  aspect_ratio_key?: string | null;
}

export interface KidsProjectDetails {
  id: string;
  slug: string;
  name: string;
  style_id?: string | null;
  style_slug?: string | null;
  has_story: boolean;
  story?: KidsStory | null;
  has_cover: boolean;
  vignettes: KidsVignetteStatus[];
}

/**
 * Fetch dell'API con gestione standardizzata di errori.
 * - credentials: 'include' invia il cookie auth
 * - 204 → returns undefined
 * - non-ok → throw Error con `detail` dal body se disponibile
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    // Token mancante/scaduto → redirect a login
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Sessione scaduta");
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
