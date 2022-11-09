<script>
  import { onDestroy } from "svelte";
  import { Router, Link, Route, navigate, createHistory } from "svelte-navigator";
  import PopupMain from "./PopupMain.svelte";
  import PopupYoutube from "./youtube/Popup.svelte";
  import PopupTwitter from "./twitter/Popup.svelte";
  import PopupHeader from "$extlib/PopupHeader.svelte";
  import PopupNoWebln from "./PopupNoWebln.svelte";
  import { apiOrigin } from "$lib/api.js";
  import { webOrigin } from "$lib/utils.js";
  import { cookies } from "$lib/session.js";
  import { worker, getCurrentTab, browser, connectToPage } from "$extlib/common.js";
  import { cLog, cInfo } from "$lib/log.js";
  import createHashSource from "$extlib/hashHistory.js";

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

<svelte:head>
  <title>Donate4.Fun</title>
</svelte:head>

<div class="popup gradient">
  <div class="inner">
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
        <Route path="twitter">
          <PopupHeader />
          <PopupTwitter bind:amount={amount} />
        </Route>
        <Route path="nowebln/:amount/:rejected" let:params>
          <PopupNoWebln amount={params.amount} rejected={params.rejected} historySource={hashSource}/>
        </Route>
      </Router>
    {/await}
  </div>
</div>

<style>
:global(body) {
  width: 380px;
  height: 600px;
  overflow: hidden;
}
.popup {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  justify-content: space-between;
}
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
.inner {
  font-size: 14px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  position: relative;
  height: 100%;
  justify-content: space-between;
}
</style>
