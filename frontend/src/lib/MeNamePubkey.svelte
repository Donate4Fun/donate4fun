<script>
  import { me } from "$lib/session.js";

  export let align = "start";
</script>

<div class="outer" style:align-items={align}>
  {#await $me then me}
    <p class="name ellipsis" title={me.donator.name}>{me.donator.name}</p>
  {/await}
</div>

<style>
.outer {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 0;
}
.name {
  font-weight: 500;
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.01em;
}
</style>
