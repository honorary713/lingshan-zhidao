<template>
  <div class="page-header">
    <h2 class="header-title">{{ title }}</h2>
    <div class="header-actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({ title: { type: String, required: true } })
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-title {
  font-family: var(--font-song);
  font-size: 20px;
  font-weight: 600;
  color: var(--ink-text);
  letter-spacing: 0.08em;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
