<script>
  import { useResolve, navigate, link } from "svelte-navigator";

  import NotFoundPage from "../routes/NotFoundPage.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import FiatAmount from "$lib/FiatAmount.svelte";
  import Button from "$lib/Button.svelte";
  import GithubUser from "$lib/GithubUser.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import { api } from "$lib/api.js";
  import title from "$lib/title.js";
  import { me } from "$lib/session.js";

  export let user_id;

  let user;
  let shareUrl;

  $: baseUrl = `social/github/${user_id}`;

  const resolve = useResolve();

  async function load() {
    user = await api.get(baseUrl);
    if (!user.is_my)
      navigate('/signin', {replace: true});
  }

  async function claim() {
    await api.post(`${baseUrl}/transfer`);
    await load();
  }

  async function loadDonations() {
    return await api.get(`${baseUrl}/donations/by-donatee`);
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then}
    <Section>
      <div class="content">
        <h1>
          <img alt=twitter src="/static/github.svg" width=20>
          Donations to <GithubUser showHandle={false} imagePlacement=after --image-size=44px user={user} />
        </h1>
        <div class="amounts">
          <Amount amount={user.balance} />
          <FiatAmount amount={user.balance} />
        </div>
        <div class="buttons">
          {#await $me then me}
            {#if me.connected}
              <Button disabled={user.balance === 0} on:click={claim} --border-width=0>Collect</Button>
            {:else}
              <Button link='/login' --border-width=0>Login</Button>
            {/if}
          {/await}
          <a use:link href={resolve("..")}>Public page</a>
        </div>
      </div>
    </Section>

    <div class="details">
      {#await loadDonations() then donations}
        <DonationsTable donations={donations} />
      {/await}
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
