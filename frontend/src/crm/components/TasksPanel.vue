<script setup lang="ts">
import { ref, onMounted } from "vue";
import { crmTasksApi, type CrmTask } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const props = defineProps<{
  leadId?: string;
  dealId?: string;
}>();

const auth = useAuthStore();
const tasks = ref<CrmTask[]>([]);
const loading = ref(true);
const newTitle = ref("");
const creating = ref(false);

onMounted(async () => {
  try {
    tasks.value = await crmTasksApi.list(auth.accessToken!, {
      lead_id: props.leadId,
      deal_id: props.dealId,
    });
  } finally {
    loading.value = false;
  }
});

async function createTask() {
  const title = newTitle.value.trim();
  if (!title || creating.value) return;
  creating.value = true;
  try {
    const task = await crmTasksApi.create(auth.accessToken!, {
      title,
      lead_id: props.leadId,
      deal_id: props.dealId,
    });
    tasks.value.push(task);
    newTitle.value = "";
  } finally {
    creating.value = false;
  }
}

async function toggleTask(task: CrmTask) {
  const newStatus = task.status === "open" ? "done" : "open";
  const updated = await crmTasksApi.update(auth.accessToken!, task.id, { status: newStatus });
  const idx = tasks.value.findIndex((t) => t.id === task.id);
  if (idx !== -1) tasks.value[idx] = updated;
}
</script>

<template>
  <div class="tasks-panel">
    <!-- Add task row -->
    <div class="flex gap-2 mb-4">
      <BaseInput
        v-model="newTitle"
        placeholder="New task…"
        class="flex-1"
        @keydown.enter="createTask"
      />
      <BaseButton :disabled="!newTitle.trim() || creating" @click="createTask">
        Add
      </BaseButton>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 3" :key="n" class="skeleton h-10 rounded-xl" />
    </div>

    <!-- Empty state -->
    <div v-else-if="tasks.length === 0" class="text-center py-8 text-muted text-sm">
      No tasks yet.
    </div>

    <!-- Task list -->
    <ul v-else class="space-y-1">
      <li
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="{ done: task.status === 'done' }"
      >
        <button
          class="task-check"
          :class="{ checked: task.status === 'done' }"
          @click="toggleTask(task)"
        >
          <span v-if="task.status === 'done'" class="text-xs">✓</span>
        </button>
        <span class="task-title text-sm">{{ task.title }}</span>
        <span v-if="task.due_date" class="text-xs text-muted ml-auto">
          {{ new Date(task.due_date).toLocaleDateString() }}
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background 100ms ease;
}

.task-item:hover { background: var(--surface-raised); }

.task-check {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 1.5px solid var(--border);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-ink);
  transition: all 120ms ease;
}

.task-check.checked {
  background: var(--accent);
  border-color: var(--accent);
}

.task-item.done .task-title {
  text-decoration: line-through;
  color: var(--muted);
}
</style>
