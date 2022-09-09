<script>
  import "inter-ui/inter.css";
  import PopupDefault from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import {webOrigin} from "../../frontend/src/lib/utils.js";
  import {me} from "../../frontend/src/lib/session.js";
  import {worker, getCurrentTab, browser, contentScript} from "./common.js";

  let showYoutube = false;

  async function load() {
    const host = await worker.getConfig("apiHost");
    apiOrigin.set(`https://${host}`);
    webOrigin.set(`https://${host}`);

    const tab = await getCurrentTab();
    if (tab.url)
      showYoutube = tab.url.match('^https\:\/\/(www\.)?youtube\.com');
    await me.init();
  }
</script>

<div class="flex-column height-full justify-space-between gradient">
{#await load() then}
  {#if showYoutube}
    <PopupYoutube />
  {:else}
    <PopupDefault />
  {/if}
{/await}
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
