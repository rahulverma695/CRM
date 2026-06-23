<script setup lang="ts">
import draggable from "vuedraggable";
import KanbanCard from "./KanbanCard.vue";
import type { Lead, PipelineStage } from "@/crm/api";

const props = defineProps<{
  stage: PipelineStage;
  leads: Lead[];
}>();

const emit = defineEmits<{
  (e: "move", leadId: string, stageId: string): void;
}>();

const localLeads = defineModel<Lead[]>("leads", { required: true });

function onDragChange(evt: { added?: { element: Lead }; moved?: { element: Lead } }) {
  if (evt.added) {
    emit("move", evt.added.element.id, props.stage.id);
  }
}
</script>

<template>
  <div class="kanban-column">
    <!-- Column header -->
    <div class="column-header">
      <div class="flex items-center gap-2 min-w-0">
        <span
          class="size-2.5 rounded-full flex-shrink-0"
          :style="{ background: stage.color }"
        />
        <span class="text-sm font-semibold text-ink truncate">{{ stage.name }}</span>
      </div>
      <span class="text-xs text-muted tabular-nums font-medium">
        {{ localLeads.length }}
      </span>
    </div>

    <!-- Drop zone -->
    <draggable
      v-model="localLeads"
      item-key="id"
      group="leads"
      ghost-class="drag-ghost"
      drag-class="drag-active"
      :animation="180"
      class="column-body"
      @change="onDragChange"
    >
      <template #item="{ element: lead }">
        <div class="stagger-item mb-2">
          <KanbanCard :lead="lead" />
        </div>
      </template>

      <template #footer>
        <div v-if="localLeads.length === 0" class="column-empty">
          Drop here
        </div>
      </template>
    </draggable>
  </div>
</template>

<style scoped>
.kanban-column {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.column-body {
  flex: 1;
  min-height: 80px;
  padding: 6px;
  border: 1px dashed transparent;
  border-radius: 12px;
  transition: border-color 150ms ease, background 150ms ease;
}

.column-body:focus-within,
.column-body.sortable-drag-over {
  border-color: var(--accent);
  background: rgba(198, 242, 78, 0.03);
}

.column-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  color: var(--muted);
  font-size: 12px;
  border: 1px dashed var(--border);
  border-radius: 8px;
}

:deep(.drag-ghost) {
  opacity: 0.35;
  border: 1px dashed var(--accent) !important;
  background: rgba(198, 242, 78, 0.06) !important;
  border-radius: 12px;
}
</style>
