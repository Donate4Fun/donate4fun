<script>
  import { useResolve } from "svelte-navigator";

  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
  import { api } from "$lib/api.js";
  import title from "$lib/title.js";

  export let account_id;

  let account;
  let donations;
  let shareUrl;

  $: baseUrl = `twitter/account/${account_id}`;
  $: {
    shareUrl = new URL('https://twitter.com/intent/tweet');
    shareUrl.searchParams.append('text', 'Donate me');
    shareUrl.searchParams.append('url', location.href);
    shareUrl.searchParams.append('via', 'donate4_fun');
  }

  const resolve = useResolve();

  async function load() {
    account = await api.get(baseUrl);
    $title = `Donate to @${account.handle} Twitter account`
    donations = await api.get(`${baseUrl}/donations/by-donatee`);
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
      <div class="youtube-channel">
        <h1>
          <img alt=youtube src="/static/twitter.svg" width=20>
          Donate to <TwitterAccount showHandle={false} imagePlacement=after --image-size=44px account={account} />
        </h1>
        <PaymentWidget target={{twitter_account_id: account.id}} on:paid={load} />
        <Button class="white" link={shareUrl} target="_blank">
          <img alt=youtube src="/static/twitter.svg" width=20>
          Share
        </Button>
      </div>
    </Section>

    <div class="details">
      <div class="controls">
        <Button class="grey" link={resolve("owner")}>This is my account</Button>
        <Button class="grey" link={resolve("link")}>Want more donations?</Button>
      </div>
      <DonationsTable donations={donations} />
    </div>
  {/await}
</div>

<style>
.container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.youtube-channel {
  padding: 36px 70px 74px;
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
  width: 640px;
}
.controls {
  display: flex;
  gap: 20px;
  align-items: center;
}
</style>
