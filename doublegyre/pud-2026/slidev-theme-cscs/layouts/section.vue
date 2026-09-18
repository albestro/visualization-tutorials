<script setup lang="ts">
import LogoHeader from '../components/LogoHeader.vue'
</script>

<template>
  <div class="slidev-layout section relative h-full w-full">
    <!-- Top logos -->
    <LogoHeader />

    <!-- Title area just above the red line -->
    <div class="absolute left-0 right-0 top-[40%] px-16 flex flex-col justify-end h-[10%]">
      <slot />
    </div>

    <!-- Red accent line at 50% -->
    <div class="absolute left-0 right-0 top-1/2 h-0.5 bg-[#a60b16]" />
  </div>
</template>
