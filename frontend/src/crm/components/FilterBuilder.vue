<script setup lang="ts">
import { ref } from "vue";
import BaseButton from "@/components/BaseButton.vue";

interface FilterRow {
  field: string;
  operator: string;
  value: string;
}

const FIELDS = [
  { label: "Company", key: "company" },
  { label: "Source", key: "source" },
  { label: "Stage", key: "stage_id" },
  { label: "Owner", key: "owner_id" },
];

const OPERATORS = ["is", "is not", "contains", "starts with"];

const props = defineProps<{
  modelValue?: FilterRow[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: FilterRow[]): void;
  (e: "apply"): void;
}>();

const rows = ref<FilterRow[]>(
  props.modelValue?.length ? [...props.modelValue] : [{ field: "company", operator: "is", value: "" }]
);

function addRow() {
  rows.value.push({ field: "company", operator: "is", value: "" });
}

function removeRow(i: number) {
  rows.value.splice(i, 1);
}

function apply() {
  emit("update:modelValue", [...rows.value]);
  emit("apply");
}
</script>

<template>
  <div class="filter-builder">
    <div
      v-for="(row, i) in rows"
      :key="i"
      class="filter-row"
    >
      <select v-model="row.field" class="filter-select">
        <option v-for="f in FIELDS" :key="f.key" :value="f.key">{{ f.label }}</option>
      </select>
      <select v-model="row.operator" class="filter-select">
        <option v-for="op in OPERATORS" :key="op" :value="op">{{ op }}</option>
      </select>
      <input
        v-model="row.value"
        placeholder="Value"
        class="filter-input"
      />
      <button
        class="remove-btn"
        :disabled="rows.length === 1"
        @click="removeRow(i)"
      >×</button>
    </div>

    <div class="flex gap-2 mt-3">
      <button class="add-filter-btn" @click="addRow">+ Add filter</button>
      <div class="ml-auto flex gap-2">
        <BaseButton @click="apply">Apply</BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-builder {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
}

.filter-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.filter-select,
.filter-input {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  color: var(--ink);
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 8px;
  outline: none;
  transition: border-color 120ms ease;
}

.filter-input { flex: 1; }
.filter-select { cursor: pointer; }

.filter-select:focus,
.filter-input:focus { border-color: var(--accent); }

.remove-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 6px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 100ms ease;
  flex-shrink: 0;
}

.remove-btn:hover:not(:disabled) { color: var(--ink); border-color: var(--ink); }
.remove-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.add-filter-btn {
  font-size: 12px;
  color: var(--muted);
  background: transparent;
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 4px 12px;
  cursor: pointer;
  transition: all 100ms ease;
}

.add-filter-btn:hover { color: var(--ink); border-color: var(--ink); }
</style>
