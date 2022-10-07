<script>
  import {onDestroy} from "svelte";
  import Lnurl from "../lib/Lnurl.svelte";
  import Button from "../lib/Button.svelte";
  import QRCode from "../lib/QRCode.svelte";
  import Section from "../lib/Section.svelte";
  import Loading from "../lib/Loading.svelte";
  import Spinner from "../lib/Spinner.svelte";
  import api from "../lib/api.js";
  import {me} from "../lib/session.js";
  import {notify} from "../lib/notifications.js";

  export let navigate;
  export let location;

  let lnurl;
  let unsubscribe = null;

  onDestroy(() => {
    if (unsubscribe !== null) {
      unsubscribe();
    }
  });

  async function load() {
    await $me.loaded;
    const params = new URLSearchParams(location.search);
    const return_ = params.get('return');
    unsubscribe = await api.subscribe("donator:" + $me.donator.id, async (token) => {
      unsubscribe();
      await api.post('update-session', {creds_jwt: token['message']});
      await $me.load();
      navigate(return_ || "/donator/" + $me.donator.id);
      if ($me.connected)
        notify("Success", `You've successefully connected your wallet`, "success");
      else
        notify("Success", `You've successefully disconnected your wallet`, "success");
    });
    const response = await api.get('lnauth');
    lnurl = response.lnurl;
  }

  async function disconnect() {
    await api.post('disconnect-wallet');
  }
</script>

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
        <a href="lightning:{lnurl}" class="open-in-wallet"><Button --width=100%>Connect using Wallet</Button></a>
        <Lnurl lnurl="{lnurl}" class="lnurl" />
        <Button class="white" on:click={$me.reset} --width=100%>Reset account</Button>
        {#if $me.donator.lnauth_pubkey}
          <Button
            class="white"
            --width=100%
            on:click={disconnect}
            disabled={$me.donator.balance > 0}
            title={$me.donator.balance > 0 ? "You can't disconnect wallet if you have funds" : ""}
          >Disconnect wallet</Button>
        {/if}
        <Button class="grey" on:click={() => navigate(-1)} --width=100%>Cancel</Button>
      </div>
      <div class=waiting>
        <Spinner /><span>Waiting for you...</span>
      </div>
    </Section>
  </div>
{/await}

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
.buttons > a {
  width: 100%;
}
div.waiting {
  display: flex;
  align-items: center;
}
</style>
