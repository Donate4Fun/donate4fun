<script>
  import { link } from "svelte-navigator";

  import Section from "$lib/Section.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Thumbnail from "$lib/Thumbnail.svelte";
  import { apiStore } from "$lib/api.js";
  import { toText } from "$lib/utils.js";

  const donatees = apiStore("donatees/top-unclaimed", "donatees");
</script>

<Section --padding=40px --width=fit-content>
  <h1>Top unclaimed donatees</h1>

  <div class="table">
    <div class="head">
      <div>Receiver</div>
      <div>Unclaimed amount</div>
    </div>
    {#if $donatees === null}
      <Loader --size=4em />
    {:else}
      {#each $donatees as donatee (donatee.id)}
        <a use:link href="/{donatee.type}/{donatee.id}" class="donatee">
          <img alt=social-logo class="social-logo" src="/static/{donatee.type}.svg">
          <Thumbnail size=3em url={donatee.thumbnail_url} />
          <span class="ellipsis">{donatee.title}</span>
        </a>
        <div>
          <Amount amount={toText(donatee.balance)} />
          <FiatAmount amount={donatee.balance} />
        </div>
      {/each}
    {/if}
  </div>
</Section>

<style>
.table .head {
  color: rgba(0, 0, 0, 0.6);
  text-align: left;
  display: contents;
}
.table {
  font-size: 12px;
  display: grid;
  grid-template-columns: 240px 199px;
  column-gap: 20px;
  row-gap: 26px;
  align-items: center;
  overflow: scroll;
  width: 100%;
}
.social-logo {
  width: 2em;
}
.donatee {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
