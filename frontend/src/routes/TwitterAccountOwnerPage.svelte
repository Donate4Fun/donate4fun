<script>
  import { useResolve, navigate, link } from "svelte-navigator";

  import NotFoundPage from "../routes/NotFoundPage.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import TwitterShare from "$lib/TwitterShare.svelte";
  import { api, socialDonationsStore } from "$lib/api.js";
  import title from "$lib/title.js";
  import { syncMe as me } from "$lib/session.js";

  export let account_id;

  let account;
  let shareUrl;

  $: baseUrl = `social/twitter/${account_id}`;

  const resolve = useResolve();

  async function load() {
    account = await api.get(baseUrl);
    if (!account.is_my)
      navigate('/signin', {replace: true});
  }

  async function claim() {
    await api.post(`${baseUrl}/transfer`);
    await load();
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then}
    <Section>
      {#if account.banner_url}
        <div class="banner" style="background-image: url({account.banner_url})"></div>
      {/if}
      <div class="content">
        <h1>
          <img alt=twitter src="/static/twitter.svg" width=20>
          Donations to <TwitterAccount showHandle={false} imagePlacement=after --image-size=44px account={account} />
        </h1>
        <div class="amounts">
          <Amount amount={account.balance} />
          <FiatAmount amount={account.balance} />
        </div>
        <div class="buttons">
          {#if $me?.connected}
            <Button disabled={account.balance === 0} on:click={claim} --border-width=0>Collect</Button>
          {:else}
            <Button link='/login' --border-width=0>Login</Button>
          {/if}
          <TwitterShare text="Donate me" />
          <a use:link href={resolve("..")}>Public page</a>
        </div>
      </div>
    </Section>

    <div class="details">
      <DonationsTable donations={socialDonationsStore('twitter', account_id)} />
    </div>
  {:catch error}
    <NotFoundPage {error} />
  {/await}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 64px;
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
.amounts {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}
.buttons {
  width: 180px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
}
.content a {
  font-weight: 600;
  font-size: 14px;
  line-height: 20px;
}
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 640px;
}
</style>
