<script>
  import { worker, contentScript, browser } from "./common.js";
  import Header from "../../frontend/src/lib/Header.svelte";

  let showDev;

  async function load() {
    showDev = await worker.getConfig('enableDevCommands');
  }
</script>
 
<Header />
<main>
  <a href={'#'} on:click={() => browser.runtime.openOptionsPage()}>Options</a>
  {#await load() then}
    {#if showDev}
      <a href={'#'} on:click={() => worker.inject()}>Inject</a>
      <a href={'#'} on:click={() => contentScript.postComment("en", 100)}>Comment</a>
    {/if}
  {/await}
  <a href="https://donate4.fun" id=website target="_blank">Website</a>
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
