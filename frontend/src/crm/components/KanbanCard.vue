<script setup lang="ts">
import type { Lead } from "@/crm/api";

const props = defineProps<{
  lead: Lead;
  isDragging?: boolean;
}>();

const initials = (lead: Lead) => {
  return `${lead.first_name[0] ?? ""}${lead.last_name[0] ?? ""}`.toUpperCase();
};
</script>

<template>
  <div
    class="kanban-card group"
    :class="{ 'is-dragging': isDragging }"
  >
    <!-- Company badge -->
    <div v-if="lead.company" class="text-xs text-muted font-medium mb-2 truncate">
      {{ lead.company }}
    </div>

    <!-- Lead name -->
    <p class="text-sm font-semibold text-ink leading-tight mb-3">
      {{ lead.first_name }} {{ lead.last_name }}
    </p>

    <!-- Footer row -->
    <div class="flex items-center justify-between gap-2">
      <!-- Source tag -->
      <span
        v-if="lead.source"
        class="text-[10px] uppercase tracking-wider text-muted bg-surface-raised px-2 py-0.5 rounded-full"
      >
        {{ lead.source }}
      </span>
      <span v-else class="flex-1" />

      <!-- Owner avatar -->
      <div
        v-if="lead.owner_id"
        class="size-6 rounded-full bg-accent/20 text-accent flex items-center justify-center text-[10px] font-bold select-none"
        :title="lead.owner_id"
      >
        {{ initials(lead) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.kanban-card {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  cursor: grab;
  transition:
    transform 150ms cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 150ms ease,
    border-color 150ms ease;
  user-select: none;
}

.kanban-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), 0 4px 16px rgba(198, 242, 78, 0.08);
  transform: translateY(-1px);
}

.kanban-card.is-dragging {
  cursor: grabbing;
  transform: rotate(2deg) scale(1.04);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 2px var(--accent);
  border-color: var(--accent);
  z-index: 9999;
}
</style>
