<script setup lang="ts">
import { ref } from "vue";
import { activitiesApi, type Activity } from "@/crm/api";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";

const props = defineProps<{
  leadId?: string;
  dealId?: string;
}>();

const emit = defineEmits<{
  (e: "added", activity: Activity): void;
}>();

const auth = useAuthStore();
const text = ref("");
const submitting = ref(false);

async function submit() {
  const trimmed = text.value.trim();
  if (!trimmed || submitting.value) return;
  submitting.value = true;
  try {
    const activity = await activitiesApi.create(auth.accessToken!, {
      lead_id: props.leadId,
      deal_id: props.dealId,
      type: "note",
      content: { text: trimmed },
    });
    emit("added", activity);
    text.value = "";
  } finally {
    submitting.value = false;
  }
}

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
}
</script>

<template>
  <div class="note-composer">
    <textarea
      v-model="text"
      placeholder="Add a note… (Cmd+Enter to submit)"
      rows="3"
      class="composer-textarea"
      @keydown="onKeydown"
    />
    <div class="flex justify-end mt-2">
      <BaseButton :disabled="!text.trim() || submitting" @click="submit">
        {{ submitting ? "Saving…" : "Add Note" }}
      </BaseButton>
    </div>
  </div>
</template>

<style scoped>
.note-composer {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  transition: border-color 150ms ease;
}

.note-composer:focus-within {
  border-color: var(--accent);
}

.composer-textarea {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: var(--ink);
  font-family: "Outfit", sans-serif;
  font-size: 14px;
  resize: none;
  line-height: 1.5;
}

.composer-textarea::placeholder {
  color: var(--muted);
}
</style>
