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
  pseudonym: string;
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
  preferred_quality: string;
  allowed_qualities: string[];
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
  grid_variant_label?: string | null;
}

// === Sceneggiatura (flusso Pro) ===

export interface ScriptDialogue {
  kind: string;
  speaker?: string | null;
  text: string;
}

export interface ScriptPanel {
  number: number;
  description: string;
  dialogues: ScriptDialogue[];
  shot_distance?: string | null;
  shot_angle?: string | null;
  mood?: string | null;
}

export interface ScriptPage {
  number: number;
  panels: ScriptPanel[];
}

export interface ProjectScript {
  source_text: string;
  has_script: boolean;
  script?: {
    logline: string;
    characters: Array<{ name: string; visual_bible: string; voice: string }>;
    pages: ScriptPage[];
  } | null;
}

// === Stili ===

export interface Style {
  id: string;
  label: string;
  category: string;
  expansion: string;
  is_handmade: boolean;
  is_custom: boolean;
}

export interface StyleList {
  styles: Style[];
  categories: string[];
}

// === Personaggi (flusso Pro) ===

export interface Character {
  id: string;
  name: string;
  visual_description: string;
  has_reference: boolean;
  created_at: string;
}

export interface CharacterList {
  characters: Character[];
}

// === Vignette + Pagine (flusso Pro) ===

export interface SceneOption {
  key: string;
  label: string;
}

export interface SceneOptions {
  shot_distances: SceneOption[];
  shot_angles: SceneOption[];
  moods: SceneOption[];
  aspect_ratios: SceneOption[];
}

export interface VignetteStatus {
  page_number: number;
  panel_number: number;
  description: string;
  dialogue_text?: string | null;
  dialogue_speaker?: string | null;
  generated: boolean;
  shot_distance?: string | null;
  shot_angle?: string | null;
  mood?: string | null;
  aspect_ratio_key?: string | null;
}

export interface VignettesList {
  vignettes: VignetteStatus[];
}

export interface PageInfo {
  page_number: number;
  grid_id: string;
  available_grids: string[];
  capacity: number;
  n_panels: number;
  show_balloons: boolean;
}

export interface PagesList {
  pages: PageInfo[];
}

// === Admin ===

export interface AdminUser {
  id: string;
  email: string;
  role: string;
  is_admin: boolean;
  is_active: boolean;
  plan: string;
  credits_total: number;
  credits_used: number;
  credits_remaining: number;
  must_change_password: boolean;
  created_at: string;
  last_login_at?: string | null;
  project_count: number;
}

export interface AdminUserList {
  users: AdminUser[];
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_count: number;
  users_by_role: Record<string, number>;
  total_projects: number;
  active_last_7_days: number;
}

export interface AdminRoleInfo {
  key: string;
  label: string;
  monthly_credits: number;
  max_projects: number;
}

// === Esplora ===

export interface EsploraAsset {
  id: string;
  section: string;
  asset_type: string;
  title: string;
  caption: string;
  author_name: string;
  author_role: string;
  position: number;
  has_image: boolean;
  image_url?: string | null;
  prompt: string;
  is_active: boolean;
}

export interface EsploraSection {
  key: string;
  label: string;
  aspect: string;
  items: EsploraAsset[];
}

export interface EsploraSectionsOut {
  sections: EsploraSection[];
}

/**
 * Upload di un'immagine per un asset Esplora (multipart/form-data).
 * Non usa apiFetch perché quello forza Content-Type application/json.
 */
export async function uploadEsploraImage(
  assetId: string,
  file: File
): Promise<EsploraAsset> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`/api/admin/esplora/assets/${assetId}/upload`, {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
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
  return res.json();
}

// ============================================================
// CREA — immagini della pagina pubblica /crea (slot fissi)
// ============================================================

export interface CreaImage {
  slot: string;
  label: string;
  aspect: string;
  default_src: string;
  section?: string; // "autori" | "kids"
  has_image: boolean;
  image_url?: string | null;
}

export interface CreaImagesOut {
  images: CreaImage[];
}

/**
 * Upload di un'immagine per uno slot CREA (multipart/form-data).
 * Non usa apiFetch perché quello forza Content-Type application/json.
 */
export async function uploadCreaImage(
  slot: string,
  file: File
): Promise<CreaImage> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`/api/admin/crea/images/${slot}/upload`, {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
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
  return res.json();
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
    let detailObj: unknown = null;
    try {
      const data = await res.json();
      detailObj = data?.detail;
      if (typeof data?.detail === "string") detail = data.detail;
      else if (data?.detail?.message) detail = data.detail.message;
    } catch {
      /* ignore */
    }
    if (
      res.status === 402 &&
      typeof detailObj === "object" &&
      detailObj !== null &&
      typeof window !== "undefined"
    ) {
      const code = (detailObj as { code?: string }).code;
      if (code === "free_to_play_exhausted" || code === "free_to_play_plan_locked") {
        const evt = new CustomEvent("snaptoon:ftp_exhausted", { detail: detailObj });
        window.dispatchEvent(evt);
      }
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
