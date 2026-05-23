<template>
  <Teleport to="body">
    <div v-if="open" class="admin-modal-overlay" @click.self="onCancel">
      <div class="admin-modal" role="dialog" aria-modal="true">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">{{ title }}</h3>
        </div>
        <div class="admin-modal__body">
          <p v-if="description" class="admin-modal__desc">{{ description }}</p>
          <input
            v-if="showInput"
            ref="inputRef"
            v-model="inputValue"
            class="admin-modal__input"
            :placeholder="inputPlaceholder"
          />
        </div>
        <div class="admin-modal__footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="onCancel">取消</button>
          <button
            type="button"
            class="btn btn-sm"
            :class="danger ? 'btn-danger' : 'btn-primary-admin'"
            :disabled="confirmDisabled"
            @click="onConfirm"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    confirmLabel?: string
    showInput?: boolean
    inputPlaceholder?: string
    inputRequired?: boolean
    danger?: boolean
    defaultValue?: string
  }>(),
  {
    confirmLabel: '确认',
    inputRequired: false,
    danger: false,
    defaultValue: '',
  },
)

const emit = defineEmits<{
  confirm: [value: string]
  cancel: []
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref('')

const confirmDisabled = computed(() => props.inputRequired && !inputValue.value.trim())

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      inputValue.value = props.defaultValue
      await nextTick()
      inputRef.value?.focus()
    }
  },
)

function onConfirm() {
  if (confirmDisabled.value) return
  emit('confirm', inputValue.value.trim())
}

function onCancel() {
  emit('cancel')
}
</script>
