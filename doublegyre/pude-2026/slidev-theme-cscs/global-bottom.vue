<script setup lang="ts">
import { ref } from 'vue'

const cscsUrls = [
  new URL('./public/cscs-logo-short.png', import.meta.url).href,
  new URL('./public/cscs-logo.png', import.meta.url).href,
]
const ethUrl = new URL('./public/eth-logo.png', import.meta.url).href

const cscsIndex = ref(0)
const cscsLoaded = ref(false)

function onCscsError() {
  if (cscsIndex.value < cscsUrls.length - 1) {
    cscsIndex.value++
  }
}
</script>

<template>
  <footer
    v-if="$nav.currentLayout !== 'cover' && $nav.currentLayout !== 'section'"
    class="absolute bottom-0 left-0 right-0 h-12 px-8 flex items-center justify-between text-xs text-black"
  >
    <img
      :src="cscsUrls[cscsIndex]"
      alt="CSCS"
      class="h-8 max-w-[5rem] object-contain"
      :class="{ hidden: !cscsLoaded }"
      @load="cscsLoaded = true"
      @error="onCscsError"
    />

    <div class="flex items-center gap-4">
      <span v-if="$nav.currentFrontmatter?.footer" class="text-gray-600">{{ $nav.currentFrontmatter.footer }}</span>
      <span class="text-gray-400">|</span>
      <span class="text-gray-600">{{ $nav.currentPage }}</span>
    </div>

    <img :src="ethUrl" alt="ETH" class="h-3 max-w-[4rem] object-contain" />
  </footer>
</template>
