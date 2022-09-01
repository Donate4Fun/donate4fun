<script>
  import { Router, Route } from "svelte-navigator";
  import PopupMain from "./PopupMain.svelte";
  import PopupYoutube from "./PopupYoutube.svelte";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import {worker} from "./common.js";

  const url = "";

  async function load() {
    const host = await worker.getConfig("apiHost");
    apiOrigin.set(`https://${host}`);
  }
</script>

{#await load() then}
  <Router ulr={url}>
    <Route path="/src/popup.html" component="{PopupMain}" />
    <Route path="/youtube" component="{PopupYoutube}" />
  </Router>
{/await}
