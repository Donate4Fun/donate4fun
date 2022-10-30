<script>
  import {onDestroy} from "svelte";
  import Lnurl from "$lib/Lnurl.svelte";
  import Button from "$lib/Button.svelte";
  import QRCode from "$lib/QRCode.svelte";
  import Section from "$lib/Section.svelte";
  import Loading from "$lib/Loading.svelte";
  import NeedHelp from "$lib/NeedHelp.svelte";
  import api from "$lib/api.js";
  import { me, resetMe, reloadMe } from "$lib/session.js";
  import {notify} from "$lib/notifications.js";
  import cLog from "$lib/log.js";

  export let navigate;
  export let location;
  let ws;

  async function load() {
    const params = new URLSearchParams(location.search);
    const return_ = params.get('return');
    const mee = await me.get();
    await ws?.close();
    const nonce = crypto.randomUUID();
    ws = await api.subscribe("lnauth:" + nonce, { autoReconnect: false });
    ws.on("notification", async (token) => {
      await ws.close();
      await api.post('update-session', {creds_jwt: token.message});
      await reloadMe();
      const mee = await me.get();
      navigate(return_ || -1);
      if (mee.connected)
        notify("Success", `You've successefully connected your wallet`, "success");
      else
        notify("Success", `You've successefully disconnected your wallet`, "success");
    });
    await ws.ready();
    const response = await api.get('lnauth/' + nonce);
    return response.lnurl;
  }
  onDestroy(() => ws?.close());

  async function disconnect() {
    await api.post('disconnect-wallet');
    await reloadMe();
  }

  async function connect(lnurl) {
    if (window.webln) {
      await window.webln.enable();
      await window.webln.lnurl(lnurl);
    } else {
      window.location = `lightning:${lnurl}`;
    }
  }
</script>

{#await $me}
  <Loading />
{:then me}
  <Section>
    <div class="main">
      <h1>
        {#if me.donator.lnauth_pubkey}
          Change wallet
        {:else}
          Connect wallet
        {/if}
      </h1>
      {#await load() then lnurl}
        <a href="lightning:{lnurl}" class="qrcode"><QRCode value={lnurl} /></a>
        <div class="buttons">
          <Button on:click={() => connect(lnurl)}>Connect using Wallet</Button>
          <Lnurl lnurl="{lnurl}" class="lnurl" />
          <Button class="white" on:click={resetMe}>Reset account</Button>
          {#if me.donator.lnauth_pubkey}
            <Button
              class="white"
              on:click={disconnect}
              disabled={me.donator.balance > 0}
              title={me.donator.balance > 0 ? "You can't disconnect wallet if you have funds" : ""}
            >Disconnect wallet</Button>
          {/if}
          <Button class="grey" on:click={() => navigate(-1)}>Cancel</Button>
          <NeedHelp />
        </div>
      {:catch err}
        <p>Catch {err}</p>
      {/await}
    </div>
  </Section>
{/await}

<style>
h1 {
  font-weight: 900;
}
.main {
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
</style>
