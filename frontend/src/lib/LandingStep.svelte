<script>
  import NumberInCircle from "$lib/NumberInCircle.svelte";
  import LandingSection from "$lib/LandingSection.svelte";
  export let number;
  export let done = false;
  export let doneText = null;
</script>

<LandingSection>
  <div class="container">
    <div class="number">
      <NumberInCircle number={number} --size=60px />
      {#if done}
        <div class="done-badge">
          <img class="galka" src="/static/galka.svg" alt="galka">
          <span>{doneText}</span>
        </div>
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
  display: flex;
  align-items: center;
  gap: 16px;
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
.done-badge {
  display: flex;
  align-items: center;
  padding: 4px 12px 4px 8px;
  gap: 8px;
  width: 188px;
  height: 32px;
  background: rgba(46, 108, 255, 0.15);
  border-radius: 100px;
}
</style>
