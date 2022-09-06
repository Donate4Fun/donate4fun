<script>
  import {get} from 'svelte/store';
  import {me} from "../../frontend/src/lib/session.js";
  import {apiOrigin} from "../../frontend/src/lib/api.js";
  import Userpic from "../../frontend/src/lib/Userpic.svelte";
  import Amount from "../../frontend/src/lib/Amount.svelte";
  import FiatAmount from "../../frontend/src/lib/FiatAmount.svelte";
  import Button from "../../frontend/src/lib/Button.svelte";
  import WalletLogin from "../../frontend/src/lib/WalletLogin.svelte";
  import DonateYoutube from "./DonateYoutube.svelte";

  const fulfillLink = get(apiOrigin) + '/fulfill/' + get(me).donator.id;
</script>

<main class="flex-column gap-41">
  <header class="flex-row justify-space-between">
    <img class=text src="/static/D.svg" alt="D" width=40px>
    <div class="flex-column gap-10">
      <p class="font-15 margin-0">{$me.donator.name}</p>
      {#if $me.donator.lnauth_pubkey}
        <p class="flex-row gap-6 font-12 font-weight-300 margin-0">Connected wallet: <span class="ellipsis font-weight-600">{$me.shortkey}</span></p>
      {/if}
    </div>
    <Userpic user={$me.donator} />
  </header>
  <section class="flex-column gap-20 align-center">
    {#if $me.donator.lnauth_pubkey}
      <div class="flex-column gap-12">
        <Amount class="font-24 font-weight-700" amount={$me.donator.balance} />
        <FiatAmount class="font-12 font-weight-400 text-align-center" amount={$me.donator.balance} />
      </div>
      <Button target=_blank link={fulfillLink} class=white>Fulfill</Button>
    {:else}
      <WalletLogin target=_blank />
    {/if}
  </section>
</main>

<style>
main {
  padding: 27px 32px 0 27px;
}
</style>
