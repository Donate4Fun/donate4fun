<script>
  import { onDestroy } from "svelte";
  import { Router, Link, Route, navigate, createHistory } from "svelte-navigator";
  import PopupDefault from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import PopupHeader from "./PopupHeader.svelte";
  import PopupNoWebln from "./PopupNoWebln.svelte";
  import { apiOrigin } from "$lib/api.js";
  import { webOrigin } from "$lib/utils.js";
  import { me, cookies } from "$lib/session.js";
  import { worker, getCurrentTab, browser, connectToPage } from "./common.js";
  import cLog from "./log.js";
  import createHashSource from "./hashHistory.js";

  const hashSource = createHashSource();
  const hashHistory = createHistory(hashSource);

  let showWeblnHelp = false;
  let amount;
  let balance;

  async function load() {
    const host = await worker.getConfig("apiHost");
    // These stores are used by scripts from /frontend/src/lib
    apiOrigin.set(host);
    webOrigin.set(host);
    cookies.set(browser.cookies);

    await me.loaded;

    try {
      const contentScript = await connectToPage();
      if (await contentScript.isVideoLoaded()) {
        cLog("detected youtube page, navigating to /youtube");
        hashHistory.navigate("youtube");
      }
    } catch (error) {
      console.log("error connecting to tab", error);
    }
  }

  function onNavigate(event) {
    console.log("navigate", event.location.pathname, event.action);
  }
	onDestroy(hashHistory.listen(onNavigate));
</script>

<div class="flex-column height-full justify-space-between gradient">
  <main class="flex-column gap-28 height-full position-relative">
    {#await load() then}
      <PopupHeader bind:balance={balance} history={hashHistory} />
      <Router history={hashHistory} primary={false}>
        <Route path="">
          <PopupDefault />
        </Route>
        <Route path="youtube">
          <PopupYoutube bind:amount={amount} />
        </Route>
        <Route path="nowebln/:amount" let:params>
          <PopupNoWebln amount={params.amount} historySource={hashSource}/>
        </Route>
      </Router>
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
