<script>
  import PopupDefault from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import PopupHeader from "./PopupHeader.svelte";
  import PopupNoWebln from "./PopupNoWebln.svelte";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import {webOrigin} from "../../frontend/src/lib/utils.js";
  import {me} from "../../frontend/src/lib/session.js";
  import {worker, getCurrentTab, browser, contentScript, isTest} from "./common.js";

  let showYoutube = false;
  let showWeblnHelp = false;
  let amount;
  let balance;

  async function load() {
    const host = await worker.getConfig("apiHost");
    apiOrigin.set(host);
    webOrigin.set(host);

    if (isTest()) {
      showYoutube = true;
    } else {
      const tab = await getCurrentTab();
      showYoutube = tab?.url?.match('^https\:\/\/(www\.)?youtube\.com') && await contentScript.isVideoLoaded();
    }
    await me.init();
  }
</script>

<div class="flex-column height-full justify-space-between gradient">
  <main class="flex-column gap-28 height-full position-relative">
    {#await load() then}
      {#if showWeblnHelp}
        <PopupNoWebln on:close={() => {showWeblnHelp = false;}} neededAmount={amount - balance}/>
      {/if}
      <PopupHeader bind:balance={balance} />
      {#if showYoutube}
        <PopupYoutube bind:amount={amount} on:weblnerror={() => {showWeblnHelp = true}} />
      {:else}
        <PopupDefault />
      {/if}
    {/await}
  </main>
</div>

<style>
.gradient {
  background: linear-gradient(
    119.1deg,
    rgba(97, 0, 255, 0.04) 18.3%,
    rgba(0, 163, 255, 0.04) 32.8%,
    rgba(255, 153, 0, 0.04) 64.24%
  ), #FFFFFF;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 2px;
}
</style>
