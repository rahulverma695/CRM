import { defineStore } from "pinia";
import { viewsApi, type CustomView } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";

export const useViewsStore = defineStore("views", {
  state: () => ({
    views: [] as CustomView[],
    activeViewId: null as string | null,
    loading: false,
  }),

  getters: {
    activeView: (s): CustomView | null =>
      s.views.find((v) => v.id === s.activeViewId) ?? null,
  },

  actions: {
    async fetchViews() {
      const token = useAuthStore().accessToken!;
      this.loading = true;
      try {
        this.views = await viewsApi.list(token);
      } finally {
        this.loading = false;
      }
    },

    async createView(data: Parameters<typeof viewsApi.create>[1]) {
      const token = useAuthStore().accessToken!;
      const view = await viewsApi.create(token, data);
      this.views.unshift(view);
      return view;
    },

    async updateView(id: string, data: Parameters<typeof viewsApi.update>[2]) {
      const token = useAuthStore().accessToken!;
      const updated = await viewsApi.update(token, id, data);
      const idx = this.views.findIndex((v) => v.id === id);
      if (idx !== -1) this.views[idx] = updated;
      return updated;
    },

    async removeView(id: string) {
      const token = useAuthStore().accessToken!;
      await viewsApi.remove(token, id);
      this.views = this.views.filter((v) => v.id !== id);
      if (this.activeViewId === id) this.activeViewId = null;
    },

    setActiveView(id: string | null) {
      this.activeViewId = id;
    },
  },
});
