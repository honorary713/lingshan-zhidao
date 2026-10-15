<template>
  <el-dialog v-model="visible" :title="title" width="420px" @close="handleCancel">
    <p>{{ message }}</p>
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="danger" @click="handleConfirm">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '确定要执行此操作吗？' }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])
const visible = ref(props.modelValue)

watch(() => props.modelValue, v => { visible.value = v })
watch(visible, v => { if (!v) emit('update:modelValue', false) })

function handleConfirm() { emit('confirm'); visible.value = false }
function handleCancel() { emit('cancel'); visible.value = false }
</script>
