<script setup lang="ts">
import { ref, onMounted } from "vue";
import { activitiesApi, type Activity } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";
import NoteComposer from "./NoteComposer.vue";

const props = defineProps<{
  leadId?: string;
  dealId?: string;
}>();

const auth = useAuthStore();
const activities = ref<Activity[]>([]);
const loading = ref(true);

onMounted(async () => {
  if (!props.leadId && !props.dealId) return;
  try {
    activities.value = await activitiesApi.list(auth.accessToken!, {
      lead_id: props.leadId,
      deal_id: props.dealId,
    });
  } finally {
    loading.value = false;
  }
});

function onNoteAdded(activity: Activity) {
  activities.value.push(activity);
}

function formatTime(ts: string) {
  const d = new Date(ts);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function activityIcon(type: string) {
  const icons: Record<string, string> = {
    note: "💬",
    task: "✅",
    email: "✉️",
    stage_change: "→",
  };
  return icons[type] ?? "•";
}

function activityText(a: Activity): string {
  if (a.type === "stage_change") {
    const content = a.content as { from?: string; to?: string };
    return `Stage changed`;
  }
  if (a.type === "note") {
    return (a.content as { text?: string }).text ?? "";
  }
  return a.type;
}
</script>

<template>
  <div class="activity-feed">
    <!-- Note composer -->
    <NoteComposer
      :lead-id="leadId"
      :deal-id="dealId"
      @added="onNoteAdded"
      class="mb-6"
    />

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-3">
      <div v-for="n in 3" :key="n" class="skeleton h-14 rounded-xl" />
    </div>

    <!-- Empty state -->
    <div v-else-if="activities.length === 0" class="empty-feed">
      No activity yet. Add a note to get started.
    </div>

    <!-- Activity list -->
    <div v-else class="feed-list">
      <div
        v-for="activity in [...activities].reverse()"
        :key="activity.id"
        class="feed-item stagger-item"
      >
        <div class="feed-icon">{{ activityIcon(activity.type) }}</div>
        <div class="feed-content">
          <p class="text-sm text-ink leading-snug">{{ activityText(activity) }}</p>
          <span class="text-xs text-muted">{{ formatTime(activity.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-feed {
  text-align: center;
  padding: 32px;
  color: var(--muted);
  font-size: 13px;
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feed-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 10px;
  transition: background 100ms ease;
}

.feed-item:hover { background: var(--surface-raised); }

.feed-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
}

.feed-content {
  flex: 1;
  min-width: 0;
}
</style>
