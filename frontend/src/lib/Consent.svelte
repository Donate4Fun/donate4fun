<script>
  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import { trackingEnabled, acceptTracking, declineTracking } from "$lib/analytics.js";
</script>

{#if $trackingEnabled === null}
<div class="root">
  <span class="text">Help us improve the service by allowing analytics cookie</span>
  <Button --width=125px --font-size=12px on:click={acceptTracking}>Accept</Button>
  <GrayButton --width=73px --font-size=12px on:click={declineTracking}>Decline</GrayButton>
</div>
{/if}

<style>
.root {
  position: sticky;
  bottom: 8px;
  right: 8px;
  align-self: end;

  display: flex;
  align-items: center;
  padding: 15px 20px 15px 24px;
  gap: 12px;

  background: rgba(65, 65, 65, 0.7);
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 12px;
}
.text {
  font-weight: 500;
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.015em;
  color: #F7F9FF;
  max-width: 200px;
}
</style>
