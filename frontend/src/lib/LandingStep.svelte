<script>
  import NumberInCircle from "$lib/NumberInCircle.svelte";
  import LandingSection from "$lib/LandingSection.svelte";
  export let number;
  export let done = false;
</script>

<LandingSection>
  <div class="container">
    <div class="number">
      <NumberInCircle number={number} --size=60px />
      {#if done}
        <img class="galka" src="/static/galka.svg" alt="galka">
      {/if}
    </div>
    <div class="content" class:done>
      <div class="image">
        <slot name=image />
      </div>
        <slot name=text />
    </div>
  </div>
</LandingSection>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 16px 48px;
  gap: 20px;
}
.number {
  align-self: start;
  position: relative;
}
.content {
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
  font-size: 18px;
  line-height: 24px;
}
.content.done {
  opacity: 0.5;
}
.image {
  height: 208px;
  display: flex;
  justify-content: center;
}
.galka {
  position: absolute;
  top: 36px;
  left: 38px;
}
</style>
