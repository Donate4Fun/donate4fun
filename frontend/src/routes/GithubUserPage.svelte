<script>
  import { useResolve, link } from "svelte-navigator";

  import NotFoundPage from "../routes/NotFoundPage.svelte";
  import Loader from "$lib/Loader.svelte";
  import Amount from "$lib/Amount.svelte";
  import Button from "$lib/Button.svelte";
  import GithubUser from "$lib/GithubUser.svelte";
  import Section from "$lib/Section.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import DonationsTable from "$lib/DonationsTable.svelte";
  import PaymentWidget from "$lib/PaymentWidget.svelte";
  import { api } from "$lib/api.js";
  import title from "$lib/title.js";

  export let user_id;

  const resolve = useResolve();

  async function load() {
    const user = await api.get(`social/github/${user_id}`);
    $title = `Donate to ${user.name} (@${user.login}) GitHub profile`;
    return user;
  }
</script>

<div class="container">
  {#await load()}
    <Loader />
  {:then user}
    <Section>
      <div class="content">
        <h1>
          <img alt=twitter src="/static/github.svg" width=20>
          Donate to <GithubUser externalLink={true} imagePlacement=after --image-size=44px user={user} />
        </h1>
        <div class="buttons">
          <PaymentWidget target={{github_user_id: user.id}} on:paid={load} />
          <a use:link href={resolve('owner')}>This is my account</a>
        </div>
      </div>
    </Section>

    <div class="details">
      <DonationsTable socialProvider=github accountId={user.id} />
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
}
.buttons {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  width: 300px;
}
</style>
