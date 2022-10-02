<script>
  import NumberInCircle from "$lib/NumberInCircle.svelte";
  import Section from "$lib/Section.svelte";
  export let number;
</script>

<Section --padding="16px 16px 32px 16px">
  <NumberInCircle number={number} --size=60px />
  <div>
    <slot />
  </div>
</Section>

<style>
div {
  display: grid;
  margin-top: 20px;
  grid-template-rows: 220px 90px;
  width: var(--width);
}
</style>
