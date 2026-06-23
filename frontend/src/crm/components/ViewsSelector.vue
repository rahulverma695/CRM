<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useViewsStore } from "@/crm/stores/views";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const views = useViewsStore();
const showSaveForm = ref(false);
const newViewName = ref("");
const saving = ref(false);

onMounted(() => {
  if (!views.views.length) views.fetchViews();
});

async function saveView() {
  const name = newViewName.value.trim();
  if (!name || saving.value) return;
  saving.value = true;
  try {
    await views.createView({ name, filters: {}, columns: [] });
    newViewName.value = "";
    showSaveForm.value = false;
  } finally {
    saving.value = false;
  }
}

async function deleteView(id: string) {
  await views.removeView(id);
}
</script>

<template>
  <div class="views-selector">
    <div class="views-header">
      <span class="text-sm font-semibold">Saved Views</span>
      <button class="add-view-btn" @click="showSaveForm = !showSaveForm">
        {{ showSaveForm ? "×" : "+ Save view" }}
      </button>
    </div>

    <!-- Save form -->
    <Transition name="slide-down">
      <div v-if="showSaveForm" class="save-form">
        <BaseInput v-model="newViewName" placeholder="View name" @keydown.enter="saveView" />
        <BaseButton :disabled="!newViewName.trim() || saving" @click="saveView">
          Save
        </BaseButton>
      </div>
    </Transition>

    <!-- View list -->
    <div v-if="views.loading" class="space-y-2 mt-3">
      <div v-for="n in 2" :key="n" class="skeleton h-8 rounded-lg" />
    </div>
    <ul v-else class="view-list">
      <li
        v-for="view in views.views"
        :key="view.id"
        class="view-item"
        :class="{ active: views.activeViewId === view.id }"
        @click="views.setActiveView(view.id === views.activeViewId ? null : view.id)"
      >
        <span class="text-sm truncate flex-1">{{ view.name }}</span>
        <span v-if="view.is_shared" class="text-[10px] text-muted">shared</span>
        <button
          class="delete-view"
          @click.stop="deleteView(view.id)"
        >×</button>
      </li>
    </ul>

    <div v-if="!views.loading && views.views.length === 0" class="text-xs text-muted text-center py-4">
      No saved views yet.
    </div>
  </div>
</template>

<style scoped>
.views-selector {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
}

.views-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.add-view-btn {
  font-size: 12px;
  color: var(--muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 100ms ease;
}

.add-view-btn:hover { color: var(--ink); }

.save-form {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.view-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.view-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 100ms ease;
}

.view-item:hover { background: var(--surface-raised); }
.view-item.active { background: rgba(198, 242, 78, 0.08); color: var(--accent); }

.delete-view {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 14px;
  opacity: 0;
  transition: opacity 100ms ease, color 100ms ease;
  padding: 0 2px;
}

.view-item:hover .delete-view { opacity: 1; }
.delete-view:hover { color: var(--ink); }

.slide-down-enter-active,
.slide-down-leave-active { transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1); }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
