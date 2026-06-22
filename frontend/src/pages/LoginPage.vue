<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const auth = useAuthStore();
const router = useRouter();

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-[100dvh] flex items-center justify-center p-4">
    <div class="w-full max-w-sm rounded-xl2 border border-border bg-surface-raised/70 backdrop-blur-md p-8 stagger-item">
      <div class="font-display text-2xl font-bold mb-1"><span class="text-accent">◆</span> Welcome back</div>
      <p class="text-muted text-sm mb-6">Sign in to your workspace</p>

      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <BaseInput v-model="email" type="email" placeholder="Email" />
        <BaseInput v-model="password" type="password" placeholder="Password" />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <BaseButton type="submit">{{ loading ? "Signing in…" : "Sign in" }}</BaseButton>
      </form>

      <a :href="`${API}/auth/google/login`"
         class="mt-3 flex items-center justify-center gap-2 rounded-xl border border-border py-2 text-sm hover:bg-surface">
        Continue with Google
      </a>

      <p class="text-sm text-muted mt-6 text-center">
        No account?
        <RouterLink to="/signup" class="text-accent">Create one</RouterLink>
      </p>
    </div>
  </div>
</template>
