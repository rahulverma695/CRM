<script setup lang="ts">
defineProps<{ height?: string; width?: string }>();
</script>

<template>
  <div class="skeleton" :style="{ height: height ?? '1rem', width: width ?? '100%' }" />
</template>
