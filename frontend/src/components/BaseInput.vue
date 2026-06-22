<script setup lang="ts">
defineProps<{ modelValue: string; type?: string; placeholder?: string }>();
defineEmits<{ (e: "update:modelValue", v: string): void }>();
</script>

<template>
  <input
    :type="type ?? 'text'"
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    class="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-base text-ink placeholder:text-muted focus:border-accent focus:outline-none"
  />
</template>
