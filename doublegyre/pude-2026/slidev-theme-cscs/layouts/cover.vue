<script setup lang="ts">
import { computed } from 'vue'
import LogoHeader from '../components/LogoHeader.vue'
import { resolveAssetUrl } from '../layoutHelper'
import defaultBgUrl from '../public/cover-bg.jpg'

const bgModules = import.meta.glob('../public/*.{jpg,jpeg,png}', { eager: true, import: 'default' })
const bgMap = Object.fromEntries(
  Object.entries(bgModules).map(([path, url]) => {
    const name = path.replace('../public/', '/')
    return [name, url]
  })
)

const props = defineProps({
  background: {
    type: String,
    default: defaultBgUrl,
  },
})

const bgUrl = computed(() => {
  const raw = props.background
  if (!raw) return undefined
  if (/^https?:\/\//.test(raw)) return `url("${raw}")`
  const mapped = bgMap[raw]
    || bgMap[`${raw}.jpg`]
    || bgMap[`${raw}.jpeg`]
    || bgMap[`${raw}.png`]
  if (mapped) return `url("${mapped}")`
  return `url("${resolveAssetUrl(raw)}")`
})
</script>

<template>
  <div class="slidev-layout cover relative h-full w-full">
    <!-- Top logos -->
    <LogoHeader />

    <!-- Decorative background band (matches PPTX y=1236663 to y=3429000) -->
    <div
      v-if="bgUrl"
      class="absolute left-0 right-0 top-[18%] h-[32%] bg-no-repeat bg-cover bg-center z-0"
      :style="{ backgroundImage: bgUrl }"
    />

    <!-- Red accent line at 50% -->
    <div class="absolute left-0 right-0 top-1/2 h-0.5 bg-[#a60b16] z-10" />

    <!-- Title / subtitle area below the line -->
    <div class="absolute left-0 right-0 top-[52%] bottom-0 px-16 pt-12 flex flex-col justify-start z-10">
      <slot />
    </div>
  </div>
</template>
