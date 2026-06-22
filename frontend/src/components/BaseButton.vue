<script setup lang="ts">
defineProps<{ variant?: "primary" | "ghost"; type?: "button" | "submit" }>();
</script>

<template>
  <button
    :type="type ?? 'button'"
    class="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-transform duration-150 active:scale-[0.97]"
    :class="variant === 'ghost'
      ? 'bg-transparent text-ink border border-border hover:bg-surface-raised'
      : 'bg-accent text-accent-ink hover:brightness-105'"
  >
    <slot />
  </button>
</template>
