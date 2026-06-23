<script setup lang="ts">
import { computed, ref } from "vue";
import KanbanColumn from "./KanbanColumn.vue";
import AppSkeleton from "@/components/AppSkeleton.vue";
import { usePipelineStore } from "@/crm/stores/pipeline";
import { useLeadsStore } from "@/crm/stores/leads";
import type { Lead } from "@/crm/api";

const pipeline = usePipelineStore();
const leadsStore = useLeadsStore();

const moving = ref<string | null>(null);

// Per-column reactive lead lists (needed for vuedraggable v-model)
const columnLeads = computed(() => {
  const map: Record<string, Lead[]> = {};
  for (const stage of pipeline.leadStages) {
    map[stage.id] = leadsStore.leadsByStage[stage.id] ?? [];
  }
  return map;
});

async function onMove(leadId: string, stageId: string) {
  if (moving.value === leadId) return;
  moving.value = leadId;
  try {
    await leadsStore.moveLead(leadId, stageId);
  } finally {
    moving.value = null;
  }
}

function getColumnLeads(stageId: string): Lead[] {
  return columnLeads.value[stageId] ?? [];
}

function setColumnLeads(stageId: string, leads: Lead[]) {
  // sync back into the store when draggable reorders within column
  for (const lead of leads) {
    if (lead.stage_id !== stageId) {
      leadsStore.patchLeadLocally({ ...lead, stage_id: stageId });
    }
  }
}
</script>

<template>
  <div class="kanban-board-wrap">
    <!-- Loading skeletons -->
    <div v-if="pipeline.loading || leadsStore.loading" class="kanban-board">
      <div v-for="n in 4" :key="n" class="kanban-column">
        <div class="skeleton h-10 mb-3 rounded-xl" />
        <div v-for="m in 3" :key="m" class="skeleton h-20 mb-2 rounded-xl" />
      </div>
    </div>

    <!-- Actual board -->
    <div v-else class="kanban-board">
      <KanbanColumn
        v-for="stage in pipeline.leadStages"
        :key="stage.id"
        :stage="stage"
        :leads="getColumnLeads(stage.id)"
        @update:leads="setColumnLeads(stage.id, $event)"
        @move="onMove"
      />

      <div v-if="pipeline.leadStages.length === 0" class="empty-board">
        <p class="text-muted text-sm">No pipeline stages yet.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kanban-board-wrap {
  overflow-x: auto;
  padding-bottom: 16px;
  scrollbar-color: var(--border) transparent;
}

.kanban-board {
  display: flex;
  gap: 16px;
  min-width: max-content;
  align-items: flex-start;
  padding: 4px 2px;
}

.empty-board {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 48px;
}
</style>
