<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const error = ref("");

onMounted(async () => {
  const raw = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(raw);
  const access = params.get("access");
  const refresh = params.get("refresh");
  if (!access || !refresh) {
    error.value = "Sign-in failed. Redirecting…";
    setTimeout(() => router.replace({ name: "login" }), 1500);
    return;
  }
  auth.setTokens({ access_token: access, refresh_token: refresh });
  try {
    await auth.fetchMe();
    router.replace({ name: "dashboard" });
  } catch {
    auth.logout();
    error.value = "Could not load your account. Redirecting…";
    setTimeout(() => router.replace({ name: "login" }), 1500);
  }
});
</script>

<template>
  <div class="min-h-[100dvh] flex items-center justify-center p-4">
    <div class="text-center">
      <p v-if="!error" class="text-muted text-sm">Signing you in…</p>
      <p v-else class="text-red-400 text-sm">{{ error }}</p>
    </div>
  </div>
</template>
