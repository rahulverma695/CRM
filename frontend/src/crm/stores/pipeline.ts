import { defineStore } from "pinia";
import { stagesApi, type PipelineStage } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";

export const usePipelineStore = defineStore("pipeline", {
  state: () => ({
    stages: [] as PipelineStage[],
    loading: false,
  }),

  getters: {
    leadStages: (s) => s.stages.filter((st) => st.type === "lead"),
    dealStages: (s) => s.stages.filter((st) => st.type === "deal"),
  },

  actions: {
    async fetchStages() {
      const token = useAuthStore().accessToken!;
      this.loading = true;
      try {
        this.stages = await stagesApi.list(token);
      } finally {
        this.loading = false;
      }
    },

    async createStage(data: { name: string; color: string; order: number; type: "lead" | "deal" }) {
      const token = useAuthStore().accessToken!;
      const stage = await stagesApi.create(token, data);
      this.stages.push(stage);
      return stage;
    },

    async updateStage(id: string, data: Partial<{ name: string; color: string; order: number }>) {
      const token = useAuthStore().accessToken!;
      const updated = await stagesApi.update(token, id, data);
      const idx = this.stages.findIndex((s) => s.id === id);
      if (idx !== -1) this.stages[idx] = updated;
      return updated;
    },

    async removeStage(id: string) {
      const token = useAuthStore().accessToken!;
      await stagesApi.remove(token, id);
      this.stages = this.stages.filter((s) => s.id !== id);
    },
  },
});
