<script setup lang="ts">
import { RouterView, useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import { onMounted } from "vue";

const auth = useAuthStore();
const router = useRouter();

onMounted(() => {
  if (auth.isAuthenticated && !auth.user) auth.fetchMe().catch(() => auth.logout());
});

function logout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="flex min-h-[100dvh]">
    <!-- Sidebar -->
    <aside class="w-60 shrink-0 border-r border-border bg-surface/60 backdrop-blur-md p-4 flex flex-col">
      <div class="font-display text-lg font-bold mb-8">
        <span class="text-accent">◆</span> Pipeline
      </div>
      <nav class="flex flex-col gap-1 text-sm">
        <RouterLink to="/" class="rounded-lg px-3 py-2 hover:bg-surface-raised" active-class="bg-surface-raised text-accent">
          Dashboard
        </RouterLink>
        <div class="mt-4 mb-1 text-xs uppercase tracking-wider text-muted px-3">CRM</div>
        <RouterLink to="/crm" class="rounded-lg px-3 py-2 hover:bg-surface-raised" active-class="bg-surface-raised text-accent">
          Pipeline
        </RouterLink>
        <div class="mt-4 mb-1 text-xs uppercase tracking-wider text-muted px-3">HR</div>
        <span class="rounded-lg px-3 py-2 text-muted cursor-not-allowed">Employees (Phase 2)</span>
      </nav>
      <div class="mt-auto">
        <div class="text-sm text-ink">{{ auth.user?.name }}</div>
        <div class="text-xs text-muted mb-2">{{ auth.user?.email }}</div>
        <button class="text-xs text-muted hover:text-ink" @click="logout">Sign out</button>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 p-6 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>
