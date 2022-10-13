<script>
  import { onDestroy } from "svelte";
  import { Router, Link, Route, navigate, createHistory } from "svelte-navigator";
  import PopupMain from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import PopupHeader from "./PopupHeader.svelte";
  import PopupNoWebln from "./PopupNoWebln.svelte";
  import { apiOrigin } from "$lib/api.js";
  import { webOrigin } from "$lib/utils.js";
  import { cookies } from "$lib/session.js";
  import { worker, getCurrentTab, browser, connectToPage } from "./common.js";
  import { cLog, cInfo } from "$lib/log.js";
  import createHashSource from "./hashHistory.js";

  const hashSource = createHashSource();
  const hashHistory = createHistory(hashSource);

  let showWeblnHelp = false;
  let amount;

  async function load() {
    const host = await worker.getConfig("apiHost");
    // These stores are used by scripts from /frontend/src/lib
    apiOrigin.set(host);
    webOrigin.set(host);
    cookies.set(browser.cookies);

    try {
      const contentScript = await connectToPage();
      if (contentScript) {
        const popupPath = await contentScript.popupPath();
        cLog("detected supported page, navigating to", popupPath);
        hashHistory.navigate(popupPath);
      } else {
        cLog("page has no assiciated content script");
      }
    } catch (error) {
      cInfo("error connecting to tab", error);
    }
  }

  function onNavigate(event) {
    cLog("navigate", event.location.pathname, event.action);
  }

	const unlistenHistory = hashHistory.listen(onNavigate);
  onDestroy(() => {
	  unlistenHistory();
  });
</script>

<div class="flex-column height-full justify-space-between gradient">
  <main class="flex-column gap-28 height-full position-relative">
    {#await load() then}
      <Router history={hashHistory} primary={false}>
        <Route path="">
          <PopupHeader />
          <PopupMain />
        </Route>
        <Route path="youtube">
          <PopupHeader />
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
main {
  font-size: 14px;
}
</style>
