<script setup lang="ts">
import { useAuthStore } from "@/core/stores/auth";
const auth = useAuthStore();
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold mb-1">
      Welcome{{ auth.user ? `, ${auth.user.name}` : "" }}
    </h1>
    <p class="text-muted mb-8">Your workspace is ready. CRM and HR modules land next.</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="(card, i) in [
          { label: 'Sales Pipeline', body: 'Kanban board for leads & deals', tag: 'Phase 1' },
          { label: 'Team & HR', body: 'Directory, attendance, leave', tag: 'Phase 2' },
          { label: 'Custom Views', body: 'Saved filters & shared views', tag: 'Phase 1' },
        ]"
        :key="i"
        class="stagger-item rounded-xl2 border border-border bg-surface-raised/70 backdrop-blur-md p-5"
        :style="{ animationDelay: `${i * 80}ms` }"
      >
        <div class="text-xs uppercase tracking-wider text-accent mb-2">{{ card.tag }}</div>
        <div class="font-display font-semibold mb-1">{{ card.label }}</div>
        <div class="text-sm text-muted">{{ card.body }}</div>
      </div>
    </div>
  </div>
</template>
