<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const token = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

onMounted(() => {
  token.value = (route.query.token as string) ?? "";
});

async function submit() {
  error.value = "";
  if (!token.value) {
    error.value = "Missing or invalid invite link.";
    return;
  }
  loading.value = true;
  try {
    await auth.acceptInvite(token.value, password.value);
    router.replace({ name: "dashboard" });
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
      <div class="font-display text-2xl font-bold mb-1"><span class="text-accent">◆</span> Accept invite</div>
      <p class="text-muted text-sm mb-6">Set a password to activate your account</p>
      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <BaseInput v-model="password" type="password" placeholder="Choose a password (min 8 chars)" />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <BaseButton type="submit">{{ loading ? "Activating…" : "Activate account" }}</BaseButton>
      </form>
    </div>
  </div>
</template>
