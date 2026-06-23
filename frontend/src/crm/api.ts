import { api } from "@/core/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface PipelineStage {
  id: string;
  tenant_id: string;
  name: string;
  color: string;
  order: number;
  type: "lead" | "deal";
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: string;
  tenant_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  stage_id: string | null;
  owner_id: string | null;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface Deal {
  id: string;
  tenant_id: string;
  lead_id: string | null;
  title: string;
  value: number | null;
  currency: string;
  stage_id: string | null;
  probability: number | null;
  expected_close_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  tenant_id: string;
  lead_id: string | null;
  deal_id: string | null;
  type: "note" | "task" | "email" | "stage_change";
  content: Record<string, unknown>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CrmTask {
  id: string;
  tenant_id: string;
  lead_id: string | null;
  deal_id: string | null;
  title: string;
  due_date: string | null;
  assignee_id: string | null;
  status: "open" | "done";
  created_at: string;
  updated_at: string;
}

export interface CustomView {
  id: string;
  tenant_id: string;
  user_id: string;
  name: string;
  filters: Record<string, unknown>;
  sort: string | null;
  columns: string[];
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

// ── Stages ───────────────────────────────────────────────────────────────────

export const stagesApi = {
  list: (token: string) =>
    api<PipelineStage[]>("/crm/stages", { token }),

  create: (token: string, data: { name: string; color: string; order: number; type: "lead" | "deal" }) =>
    api<PipelineStage>("/crm/stages", { method: "POST", token, body: data }),

  update: (token: string, id: string, data: Partial<{ name: string; color: string; order: number }>) =>
    api<PipelineStage>(`/crm/stages/${id}`, { method: "PATCH", token, body: data }),

  remove: (token: string, id: string) =>
    api<void>(`/crm/stages/${id}`, { method: "DELETE", token }),
};

// ── Leads ────────────────────────────────────────────────────────────────────

export interface LeadFilters {
  stage_id?: string;
  owner_id?: string;
}

export const leadsApi = {
  list: (token: string, filters: LeadFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.stage_id) params.set("stage_id", filters.stage_id);
    if (filters.owner_id) params.set("owner_id", filters.owner_id);
    const qs = params.toString() ? `?${params}` : "";
    return api<Lead[]>(`/crm/leads${qs}`, { token });
  },

  get: (token: string, id: string) =>
    api<Lead>(`/crm/leads/${id}`, { token }),

  create: (token: string, data: {
    first_name: string;
    last_name: string;
    email?: string;
    phone?: string;
    company?: string;
    stage_id?: string;
    owner_id?: string;
    source?: string;
  }) => api<Lead>("/crm/leads", { method: "POST", token, body: data }),

  update: (token: string, id: string, data: Partial<Omit<Lead, "id" | "tenant_id" | "created_at" | "updated_at">>) =>
    api<Lead>(`/crm/leads/${id}`, { method: "PATCH", token, body: data }),

  remove: (token: string, id: string) =>
    api<void>(`/crm/leads/${id}`, { method: "DELETE", token }),
};

// ── Deals ────────────────────────────────────────────────────────────────────

export const dealsApi = {
  list: (token: string, filters: { lead_id?: string; stage_id?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.lead_id) params.set("lead_id", filters.lead_id);
    if (filters.stage_id) params.set("stage_id", filters.stage_id);
    const qs = params.toString() ? `?${params}` : "";
    return api<Deal[]>(`/crm/deals${qs}`, { token });
  },

  get: (token: string, id: string) =>
    api<Deal>(`/crm/deals/${id}`, { token }),

  create: (token: string, data: {
    title: string;
    lead_id?: string;
    value?: number;
    currency?: string;
    stage_id?: string;
    probability?: number;
    expected_close_date?: string;
  }) => api<Deal>("/crm/deals", { method: "POST", token, body: data }),

  update: (token: string, id: string, data: Partial<Omit<Deal, "id" | "tenant_id" | "created_at" | "updated_at">>) =>
    api<Deal>(`/crm/deals/${id}`, { method: "PATCH", token, body: data }),

  remove: (token: string, id: string) =>
    api<void>(`/crm/deals/${id}`, { method: "DELETE", token }),
};

// ── Activities ───────────────────────────────────────────────────────────────

export const activitiesApi = {
  list: (token: string, filters: { lead_id?: string; deal_id?: string }) => {
    const params = new URLSearchParams();
    if (filters.lead_id) params.set("lead_id", filters.lead_id);
    if (filters.deal_id) params.set("deal_id", filters.deal_id);
    return api<Activity[]>(`/crm/activities?${params}`, { token });
  },

  create: (token: string, data: {
    lead_id?: string;
    deal_id?: string;
    type: "note" | "task" | "email";
    content: Record<string, unknown>;
  }) => api<Activity>("/crm/activities", { method: "POST", token, body: data }),
};

// ── Tasks ────────────────────────────────────────────────────────────────────

export const crmTasksApi = {
  list: (token: string, filters: { lead_id?: string; deal_id?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.lead_id) params.set("lead_id", filters.lead_id);
    if (filters.deal_id) params.set("deal_id", filters.deal_id);
    const qs = params.toString() ? `?${params}` : "";
    return api<CrmTask[]>(`/crm/tasks${qs}`, { token });
  },

  create: (token: string, data: {
    title: string;
    lead_id?: string;
    deal_id?: string;
    due_date?: string;
    assignee_id?: string;
  }) => api<CrmTask>("/crm/tasks", { method: "POST", token, body: data }),

  update: (token: string, id: string, data: Partial<{ title: string; due_date: string; status: "open" | "done"; assignee_id: string }>) =>
    api<CrmTask>(`/crm/tasks/${id}`, { method: "PATCH", token, body: data }),

  remove: (token: string, id: string) =>
    api<void>(`/crm/tasks/${id}`, { method: "DELETE", token }),
};

// ── Custom Views ─────────────────────────────────────────────────────────────

export const viewsApi = {
  list: (token: string) =>
    api<CustomView[]>("/crm/views", { token }),

  create: (token: string, data: { name: string; filters?: Record<string, unknown>; sort?: string; columns?: string[]; is_shared?: boolean }) =>
    api<CustomView>("/crm/views", { method: "POST", token, body: data }),

  update: (token: string, id: string, data: Partial<{ name: string; filters: Record<string, unknown>; sort: string; columns: string[]; is_shared: boolean }>) =>
    api<CustomView>(`/crm/views/${id}`, { method: "PATCH", token, body: data }),

  remove: (token: string, id: string) =>
    api<void>(`/crm/views/${id}`, { method: "DELETE", token }),
};
