<script>
  import { slide } from 'svelte/transition';

  import NotFoundPage from "../routes/NotFoundPage.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
  import TwitterShare from "$lib/TwitterShare.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import Title from "$lib/Title.svelte";
  import { api, socialDonationsStore, apiStore } from "$lib/api.js";
  import { toText, capitalize } from "$lib/utils.js";

  export let provider;
  export let account_id;

  const account = apiStore(`social/${provider}/${account_id}`, `social:${provider}:${account_id}`);
</script>

<div class="container">
  {#if $account === null}
    <Loader />
  {:else}
    <Title title="Donate to {$account.name} {capitalize(provider)} account" />
    <Section>
      {#if $account.banner_url}
        <div class="banner" style="background-image: url({$account.banner_url})"></div>
      {/if}
      <div class="content">
        <h1>
          <img alt={provider} src="/static/{provider}.svg" width=20>
          Donate to <slot name="target" account={$account} />
        </h1>
        <div class="buttons">
          <PaymentWidget target={{social_provider: provider, social_account_id: account_id}} />
          <TwitterShare text="Donate to me" />
          {#if $account.balance > 0}
            <p class="unclaimed" transition:slide>
              Unclaimed: <Amount amount={toText($account.balance)} /><FiatAmount amount={$account.balance} />
            </p>
            <SocialSigninButton idp={provider}>Sign in with {capitalize(provider)} to claim</SocialSigninButton>
          {/if}
        </div>
      </div>
    </Section>

    <div class="details">
      <DonationsTable donations={socialDonationsStore(provider, account_id)} />
    </div>
  {/if}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.content {
  padding: 40px 70px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
  width: 640px;
  box-sizing: border-box;
}
.banner {
  width: 100%;
  height: 102px;
  background-repeat: no-repeat;
  background-size: 100%;
  background-position: center;
  border-top-left-radius: inherit;
  border-top-right-radius: inherit;
}
h1 {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 22px;
  font-weight: 400;
}
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.unclaimed {
  display: flex;
  align-items: end;
  gap: 1em;
}
.buttons {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  width: 300px;
}
</style>
