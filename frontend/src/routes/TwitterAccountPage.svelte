<script>
  import { useResolve, link } from "svelte-navigator";

  import NotFoundPage from "../routes/NotFoundPage.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
  import TwitterShare from "$lib/TwitterShare.svelte";
  import { api } from "$lib/api.js";
  import title from "$lib/title.js";

  export let account_id;

  let account;
  let donations;
  let shareUrl;

  $: baseUrl = `twitter/account/${account_id}`;

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
      <div class="content">
        <h1>
          <img alt=twitter src="/static/twitter.svg" width=20>
          Donate to <TwitterAccount showHandle={false} imagePlacement=after --image-size=44px account={account} />
        </h1>
        <div class="buttons">
          <PaymentWidget target={{twitter_account_id: account.id}} on:paid={load} />
          <TwitterShare text="Donate me" />
          <a use:link href={resolve('owner')}>This is my account</a>
        </div>
      </div>
    </Section>

    <div class="details">
      <DonationsTable donations={donations} />
    </div>
  {:catch error}
    <NotFoundPage {error} />
  {/await}
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
.content a {
  font-weight: 600;
  font-size: 12px;
  line-height: 20px;
}
.details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 640px;
}
.buttons {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  width: 300px;
}
</style>
