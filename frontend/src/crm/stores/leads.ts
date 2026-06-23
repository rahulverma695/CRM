import { defineStore } from "pinia";
import { leadsApi, type Lead, type LeadFilters } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";

export const useLeadsStore = defineStore("leads", {
  state: () => ({
    leads: [] as Lead[],
    loading: false,
    filters: {} as LeadFilters,
  }),

  getters: {
    leadsByStage: (s): Record<string, Lead[]> => {
      const map: Record<string, Lead[]> = {};
      for (const lead of s.leads) {
        const key = lead.stage_id ?? "__none__";
        if (!map[key]) map[key] = [];
        map[key].push(lead);
      }
      return map;
    },
  },

  actions: {
    async fetchLeads(filters: LeadFilters = {}) {
      const token = useAuthStore().accessToken!;
      this.loading = true;
      this.filters = filters;
      try {
        this.leads = await leadsApi.list(token, filters);
      } finally {
        this.loading = false;
      }
    },

    async createLead(data: Parameters<typeof leadsApi.create>[1]) {
      const token = useAuthStore().accessToken!;
      const lead = await leadsApi.create(token, data);
      this.leads.unshift(lead);
      return lead;
    },

    async updateLead(id: string, data: Parameters<typeof leadsApi.update>[2]) {
      const token = useAuthStore().accessToken!;
      const updated = await leadsApi.update(token, id, data);
      const idx = this.leads.findIndex((l) => l.id === id);
      if (idx !== -1) this.leads[idx] = updated;
      return updated;
    },

    // Optimistic move — updates locally first, then syncs to server
    async moveLead(id: string, newStageId: string) {
      const idx = this.leads.findIndex((l) => l.id === id);
      if (idx === -1) return;
      const prevStageId = this.leads[idx].stage_id;
      this.leads[idx] = { ...this.leads[idx], stage_id: newStageId };
      try {
        const token = useAuthStore().accessToken!;
        await leadsApi.update(token, id, { stage_id: newStageId });
      } catch {
        // roll back on failure
        this.leads[idx] = { ...this.leads[idx], stage_id: prevStageId };
        throw new Error("Failed to move lead");
      }
    },

    patchLeadLocally(lead: Lead) {
      const idx = this.leads.findIndex((l) => l.id === lead.id);
      if (idx !== -1) this.leads[idx] = lead;
      else this.leads.unshift(lead);
    },

    async removeLead(id: string) {
      const token = useAuthStore().accessToken!;
      await leadsApi.remove(token, id);
      this.leads = this.leads.filter((l) => l.id !== id);
    },
  },
});
