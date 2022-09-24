<script>
  import { onDestroy } from "svelte";
  import { Router, Link, Route, navigate, createHistory } from "svelte-navigator";
  import PopupDefault from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import PopupHeader from "./PopupHeader.svelte";
  import PopupNoWebln from "./PopupNoWebln.svelte";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import {webOrigin} from "../../frontend/src/lib/utils.js";
  import {me} from "../../frontend/src/lib/session.js";
  import {worker, getCurrentTab, browser, contentScript, isTest} from "./common.js";
  import createHashSource from "./hashHistory.js";

  const hashSource = createHashSource();
  const hashHistory = createHistory(hashSource);

  let showYoutube = false;
  let showWeblnHelp = false;
  let amount;
  let balance;

  async function load() {
    const host = await worker.getConfig("apiHost");
    apiOrigin.set(host);
    webOrigin.set(host);

    await me.init();
  }

  function onNavigate(event) {
    console.log("navigate", event.location.pathname, event.action);
  }
  const unlisten = hashHistory.listen(onNavigate);
	onDestroy(unlisten);
</script>

<div class="flex-column height-full justify-space-between gradient">
  <main class="flex-column gap-28 height-full position-relative">
{#await load() then}
  <Router history={hashHistory}>
    <Route path="">
      <PopupHeader bind:balance={balance} />
      <PopupDefault />
    </Route>
    <Route path="youtube">
      <PopupHeader bind:balance={balance} />
      <PopupYoutube bind:amount={amount} />
    </Route>
    <Route path="nowebln/:amount" let:params>
      <PopupHeader bind:balance={balance} />
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
