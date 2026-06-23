<script setup lang="ts">
defineProps<{ items: unknown[] }>();
</script>

<template>
  <div>
    <div
      v-for="(item, i) in items"
      :key="i"
      class="stagger-item"
      :style="{ animationDelay: `${i * 70}ms` }"
    >
      <slot :item="item" :index="i" />
    </div>
  </div>
</template>
