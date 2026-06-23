<script setup lang="ts">
import { onMounted, onUnmounted, ref, reactive } from "vue";
import KanbanBoard from "@/crm/components/KanbanBoard.vue";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";
import { usePipelineStore } from "@/crm/stores/pipeline";
import { useLeadsStore } from "@/crm/stores/leads";
import { useAuthStore } from "@/core/stores/auth";
import { createKanbanSocket, type TenantSocket } from "@/core/ws";

const pipeline = usePipelineStore();
const leadsStore = useLeadsStore();
const auth = useAuthStore();

let socket: TenantSocket | null = null;

const showNewLead = ref(false);
const creating = ref(false);
const newLead = reactive({
  first_name: "",
  last_name: "",
  email: "",
  company: "",
  stage_id: "",
});

onMounted(async () => {
  await Promise.all([
    pipeline.fetchStages(),
    leadsStore.fetchLeads(),
  ]);
  if (!newLead.stage_id && pipeline.leadStages.length) {
    newLead.stage_id = pipeline.leadStages[0].id;
  }

  if (auth.accessToken) {
    socket = createKanbanSocket(auth.accessToken);
    socket.on((msg) => {
      const ev = msg as Record<string, unknown>;
      if (ev.event === "lead_moved") {
        const existing = leadsStore.leads.find((l) => l.id === ev.lead_id);
        if (existing) {
          leadsStore.patchLeadLocally({ ...existing, stage_id: ev.stage_id as string | null });
        }
      }
    });
    socket.connect();
  }
});

onUnmounted(() => {
  socket?.disconnect();
  socket = null;
});

async function createLead() {
  if (!newLead.first_name || !newLead.last_name) return;
  creating.value = true;
  try {
    await leadsStore.createLead({
      first_name: newLead.first_name,
      last_name: newLead.last_name,
      email: newLead.email || undefined,
      company: newLead.company || undefined,
      stage_id: newLead.stage_id || undefined,
    });
    Object.assign(newLead, { first_name: "", last_name: "", email: "", company: "" });
    showNewLead.value = false;
  } finally {
    creating.value = false;
  }
}
</script>

<template>
  <div class="crm-page">
    <!-- Page header -->
    <div class="flex items-center justify-between mb-6 gap-4">
      <div>
        <h1 class="font-display text-2xl font-bold">Pipeline</h1>
        <p class="text-sm text-muted mt-0.5">{{ leadsStore.leads.length }} lead{{ leadsStore.leads.length !== 1 ? 's' : '' }}</p>
      </div>
      <BaseButton @click="showNewLead = !showNewLead">
        + New Lead
      </BaseButton>
    </div>

    <!-- New lead form -->
    <Transition name="slide-down">
      <div v-if="showNewLead" class="new-lead-form mb-6">
        <h3 class="font-semibold text-sm mb-4">New Lead</h3>
        <div class="grid grid-cols-2 gap-3 mb-3">
          <BaseInput v-model="newLead.first_name" placeholder="First name" />
          <BaseInput v-model="newLead.last_name" placeholder="Last name" />
          <BaseInput v-model="newLead.email" placeholder="Email" type="email" />
          <BaseInput v-model="newLead.company" placeholder="Company" />
        </div>
        <div class="flex items-center gap-3">
          <select
            v-model="newLead.stage_id"
            class="flex-1 rounded-xl bg-surface border border-border text-ink text-sm px-3 py-2 outline-none focus:border-accent"
          >
            <option v-for="s in pipeline.leadStages" :key="s.id" :value="s.id">
              {{ s.name }}
            </option>
          </select>
          <BaseButton type="submit" :disabled="creating" @click="createLead">
            {{ creating ? "Creating…" : "Create" }}
          </BaseButton>
          <BaseButton variant="ghost" @click="showNewLead = false">
            Cancel
          </BaseButton>
        </div>
      </div>
    </Transition>

    <!-- Kanban board -->
    <KanbanBoard />
  </div>
</template>

<style scoped>
.crm-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.new-lead-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 250ms cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
