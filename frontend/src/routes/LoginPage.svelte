<script>
  import Lnurl from "../lib/Lnurl.svelte";
  import Button from "../lib/Button.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Page from "../lib/Page.svelte";
  import Section from "../lib/Section.svelte";
  import Loading from "../lib/Loading.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import api from "../lib/api.js";
  import {me} from "../lib/session.js";

  export let navigate;
  let lnurl;

  async function load() {
    await me.init();
    api.subscribe(`donator:${$me.donator.id}`, async (token) => {
      await api.post('update-session', {creds_jwt: token['message']});
      await me.load();
      navigate(-1);
    });
    const response = await api.get('lnauth');
    lnurl = response.lnurl;
  }
</script>

<Page>
  {#await load()}
  <Loading />
  {:then}
  <div>
    <Section>
      <h1>
      {#if $me.donator.lnauth_pubkey}
      Change wallet
      {:else}
      Connect wallet
      {/if}
      </h1>
      <a href="lightning:{lnurl}" class="qrcode"><QRCode value={lnurl} /></a>
      <div class="buttons">
        <a href="lightning:{lnurl}" class="open-in-wallet"><Button>Open in wallet</Button></a>
        <Lnurl lnurl="{lnurl}" class="lnurl" />
        <Button class="grey" on:click={() => navigate(-1)}>Cancel</Button>
      </div>
      <div class=waiting><Spinner />Waiting for you...</div>
    </Section>
  </div>
  {/await}
</Page>

<style>
h1 {
  font-weight: 900;
}
div > :global(section) {
  width: 640px;
  padding: 36px 172px 54px 172px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
a.qrcode {
  margin-top: 40px;
  margin-bottom: 32px;
}
div.buttons {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1em;
  align-items: center;
  margin-bottom: 40px;
}
.buttons > :global(*) {
  width: 100%;
}
.buttons > a > :global(*) {
  width: 100%;
}
div.waiting {
  display: flex;
  align-items: center;
}
</style>
