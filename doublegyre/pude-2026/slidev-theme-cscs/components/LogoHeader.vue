<script setup lang="ts">
const cscsUrl = new URL('../public/cscs-logo.png', import.meta.url).href
const ethUrl = new URL('../public/eth-logo.png', import.meta.url).href
</script>

<template>
  <div class="absolute top-0 left-0 right-0 flex items-start justify-between px-8 pt-6 z-20">
    <img :src="cscsUrl" alt="CSCS" class="h-12 max-w-[12rem] object-contain" />
    <img :src="ethUrl" alt="ETH" class="h-4 max-w-[6rem] object-contain" />
  </div>
</template>
