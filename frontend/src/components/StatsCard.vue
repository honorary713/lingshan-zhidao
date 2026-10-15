<template>
  <div class="stats-card">
    <div class="card-icon" :style="{ background: bgColor }">
      <el-icon :size="20"><component :is="icon" /></el-icon>
    </div>
    <div class="card-body">
      <div class="card-value">{{ value }}</div>
      <div class="card-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: Object, required: true },
  bgColor: { type: String, default: 'rgba(160,132,76,0.85)' },
  value: { type: [String, Number], default: 0 },
  label: { type: String, default: '' }
})
</script>

<style scoped>
.stats-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--paper-surface);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  transition: box-shadow 0.2s;
}
.stats-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.card-icon {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.card-value {
  font-size: 26px;
  font-weight: 600;
  color: var(--ink-text);
  line-height: 1.1;
  font-feature-settings: "tnum";
}

.card-label {
  font-size: 13px;
  color: var(--ink-text-tertiary);
  margin-top: 2px;
  font-weight: 300;
  letter-spacing: 0.03em;
}
</style>
