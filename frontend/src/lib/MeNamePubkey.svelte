<script>
  import { me } from "$lib/session.js";
</script>

<div class="flex-column align-center justify-center gap-10">
  {#await $me then me}
    <p class="name">{me.donator.name}</p>
    {#if me.connected}
      <p class="flex-row gap-6 font-12 font-weight-300 margin-0">Connected wallet: <span class="ellipsis font-weight-600">{me.shortkey}</span></p>
    {/if}
  {/await}
</div>

<style>
.name {
  font-weight: 400;
  font-size: 12px;
  line-height: 18px;
  letter-spacing: 0.01em;
  margin: 0;
}
</style>
