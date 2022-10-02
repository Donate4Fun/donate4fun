<script>
  import NumberInCircle from "$lib/NumberInCircle.svelte";
  export let number;
</script>

<div class="flex-row gap-12 align-center">
  <NumberInCircle number={number} />
  <slot />
</div>
