<script>
  import { fade } from 'svelte/transition';

  export let show;
</script>

{#if show}
  <div transition:fade="{{ duration: 200 }}" class="overlay" on:click={() => show = false}>
    <div class="popup" on:click|stopPropagation={() => {}}>
      <img class="close" on:click={() => show = false} alt=close src="/static/cross.svg">
      <slot />
    </div>
  </div>
{/if}

<style>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(119.1deg, rgba(97, 0, 255, 0.04) 18.3%, rgba(0, 163, 255, 0.04) 32.8%, rgba(255, 153, 0, 0.04) 64.24%), rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.overlay .popup {
  width: 640px;
  border-radius: 24px;
  background: white;
  box-shadow: 0px 25.6px 57.6px rgba(0, 0, 0, 0.22);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.close {
  align-self: end;
  cursor: pointer;
}
</style>
