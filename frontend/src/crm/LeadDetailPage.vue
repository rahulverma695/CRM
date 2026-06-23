<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { useLeadsStore } from "@/crm/stores/leads";
import { usePipelineStore } from "@/crm/stores/pipeline";
import { leadsApi, type Lead } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";
import ActivityFeed from "@/crm/components/ActivityFeed.vue";
import TasksPanel from "@/crm/components/TasksPanel.vue";

const route = useRoute();
const auth = useAuthStore();
const leadsStore = useLeadsStore();
const pipeline = usePipelineStore();

const lead = ref<Lead | null>(null);
const loading = ref(true);
const activeTab = ref<"activity" | "tasks">("activity");

const leadId = computed(() => route.params.id as string);

const currentStageIndex = computed(() => {
  if (!lead.value) return -1;
  return pipeline.leadStages.findIndex((s) => s.id === lead.value!.stage_id);
});

onMounted(async () => {
  await Promise.all([
    pipeline.leadStages.length === 0 ? pipeline.fetchStages() : Promise.resolve(),
  ]);
  try {
    lead.value = await leadsApi.get(auth.accessToken!, leadId.value);
  } finally {
    loading.value = false;
  }
});

async function setStage(stageId: string) {
  if (!lead.value) return;
  lead.value = { ...lead.value, stage_id: stageId };
  await leadsStore.updateLead(leadId.value, { stage_id: stageId });
}
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="loading" class="lead-detail">
    <div class="skeleton h-8 w-48 mb-4 rounded-xl" />
    <div class="skeleton h-64 rounded-2xl" />
  </div>

  <!-- Lead not found -->
  <div v-else-if="!lead" class="flex flex-col items-center justify-center h-64 gap-4">
    <p class="text-muted">Lead not found.</p>
    <RouterLink to="/crm" class="text-accent text-sm hover:underline">← Back to Pipeline</RouterLink>
  </div>

  <!-- Lead detail -->
  <div v-else class="lead-detail">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm text-muted mb-6">
      <RouterLink to="/crm" class="hover:text-ink">Pipeline</RouterLink>
      <span>/</span>
      <span class="text-ink">{{ lead.first_name }} {{ lead.last_name }}</span>
    </div>

    <!-- Two-column layout -->
    <div class="detail-grid">
      <!-- Left: main content -->
      <div class="detail-main">
        <!-- Header card -->
        <div class="detail-card mb-4">
          <h1 class="font-display text-2xl font-bold mb-1">
            {{ lead.first_name }} {{ lead.last_name }}
          </h1>
          <p v-if="lead.company" class="text-muted text-sm">{{ lead.company }}</p>

          <!-- Stage pills -->
          <div class="stage-pills mt-4">
            <button
              v-for="(stage, i) in pipeline.leadStages"
              :key="stage.id"
              class="stage-pill"
              :class="{
                'is-active': stage.id === lead.stage_id,
                'is-past': i < currentStageIndex,
              }"
              @click="setStage(stage.id)"
            >
              <span
                class="size-1.5 rounded-full inline-block mr-1.5"
                :style="{ background: stage.color }"
              />
              {{ stage.name }}
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs mb-4">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'activity' }"
            @click="activeTab = 'activity'"
          >Activity</button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'tasks' }"
            @click="activeTab = 'tasks'"
          >Tasks</button>
        </div>

        <!-- Tab content -->
        <ActivityFeed v-if="activeTab === 'activity'" :lead-id="leadId" />
        <TasksPanel v-else-if="activeTab === 'tasks'" :lead-id="leadId" />
      </div>

      <!-- Right: sidebar -->
      <div class="detail-sidebar">
        <div class="detail-card">
          <h3 class="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Contact</h3>
          <dl class="space-y-3">
            <div v-if="lead.email">
              <dt class="text-xs text-muted">Email</dt>
              <dd class="text-sm">{{ lead.email }}</dd>
            </div>
            <div v-if="lead.phone">
              <dt class="text-xs text-muted">Phone</dt>
              <dd class="text-sm">{{ lead.phone }}</dd>
            </div>
            <div v-if="lead.source">
              <dt class="text-xs text-muted">Source</dt>
              <dd class="text-sm capitalize">{{ lead.source }}</dd>
            </div>
            <div>
              <dt class="text-xs text-muted">Created</dt>
              <dd class="text-sm">{{ new Date(lead.created_at).toLocaleDateString() }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lead-detail {
  max-width: 1100px;
  margin: 0 auto;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  align-items: start;
}

@media (max-width: 768px) {
  .detail-grid { grid-template-columns: 1fr; }
}

.detail-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
}

.detail-sidebar .detail-card {
  position: sticky;
  top: 20px;
}

/* Stage pills */
.stage-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.stage-pill {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  transition: all 120ms ease;
}

.stage-pill:hover { border-color: var(--ink); color: var(--ink); }

.stage-pill.is-past {
  color: var(--muted);
  border-color: var(--border);
  background: var(--surface-raised);
  opacity: 0.6;
}

.stage-pill.is-active {
  color: var(--accent-ink);
  background: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 2px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 120ms ease;
}

.tab-btn:hover { color: var(--ink); }
.tab-btn.active { background: var(--surface-raised); color: var(--ink); }
</style>
