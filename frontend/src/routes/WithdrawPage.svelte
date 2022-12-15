<script>
  import { createEventDispatcher, onDestroy } from "svelte";
  import { get } from "svelte/store";
  import { link, useResolve } from "svelte-navigator";

  import Loading from "$lib/Loading.svelte";
  import Donator from "$lib/Donator.svelte";
  import Amount from "$lib/Amount.svelte";
  import Error from "$lib/Error.svelte";
  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import Lnurl from "$lib/Lnurl.svelte";
  import Section from "$lib/Section.svelte";
  import QRCode from "$lib/QRCode.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import title from "$lib/title.js";
  import api from "$lib/api.js";
  import { notify } from "$lib/notifications.js";
  import { me } from "$lib/session.js";

  export let navigate;

  let amount;
  let ws;
  onDestroy(() => ws?.close());

  async function load() {
    try {
      const me_ = await get(me);
      const response = await api.get("me/withdraw");
      title.set(`Withdraw ${response.amount} sats`);
      ws = await api.subscribe(`withdrawal:${response.withdrawal_id}`);
      ws.on("notification", async (msg) => {
        await ws.close();
        if (msg.status === 'ERROR') {
          notify(msg.message);
        } else {
          notify("Success", "Your funds were successefully withdrawed", "success");
          navigate(`/donator/${me_.donator.id}`);
        }
      });
      await ws.ready();
      return response;
    } catch (err) {
      console.log(err);
      if (err.response.status === 403 || (err.response.data.status === 'error' && err.response.data.type === 'ValidationError'))
        navigate(".");
    }
  }
</script>

<Section>
  <div class="withdraw">
    {#await load() then { lnurl, amount }}
      <h1>Withdraw <Amount amount={amount} /></h1>
      <div>Scan with your Lightning Wallet</div>
      <a class="qrcode" href="lightning:{lnurl}"><QRCode value={lnurl} /></a>
      <div class="buttons">
        <a href="lightning:{lnurl}" class="open-in-wallet"><Button>Open in wallet</Button></a>
        <Lnurl lnurl={lnurl} class="lnurl" />
        <GrayButton on:click={() => navigate(-1)}>Cancel</GrayButton>
      </div>
      <div class="suggestion">
        Don’t have a wallet? Download wallet and claim your donations with a Wallet Like
        <a href="https://getalby.com" target="_blank">Alby</a>,
        <a href="https://phoenix.acinq.co" target="_blank">Phoenix</a>,
        <a href="https://sbw.app" target="_blank">SBW</a> or
        <a href="https://blixtwallet.github.io" target="_blank">Blixt</a>
        .
      </div>
    {/await}
  </div>
</Section>

<style>
.withdraw {
  padding: 40px 120px 74px 120px;
  display: flex;
  gap: 8px;
  flex-direction: column;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
h1 {
  text-align: center;
  font-weight: 900;
  font-size: 24px;
}
.qrcode {
  margin-top: 16px;
}
.buttons {
  width: 310px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.buttons .open-in-wallet {
  margin-top: 24px;
  width: 100%;
}
.buttons :global(.lnurl) {
  margin-top: 20px;
  margin-bottom: 32px;
  width: 100%;
}
.buttons :global(button) {
  width: 100%;
}
.suggestion {
  font-size: 16px;
  text-align: center;
}
</style>
