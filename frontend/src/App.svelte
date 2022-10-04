<script>
  import { Router, Link, Route } from "svelte-navigator";
  import Page from "$lib/Page.svelte";
  import title from "$lib/title.js";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import FulfillPage from "./routes/FulfillPage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";
  import WithdrawPage from "./routes/WithdrawPage.svelte";
  import YoutubeLinkPage from "./routes/YoutubeLinkPage.svelte";
  import YoutubeProvePage from "./routes/YoutubeProvePage.svelte";
  import LoginPage from "./routes/LoginPage.svelte";
  import Test from "./routes/Test.svelte";
  import Landing from "./routes/Landing.svelte";

  const url = "";
</script>

<svelte:head>
  <link href="/static/global.css" rel="stylesheet">
  <link href="/static/defaults.css" rel="stylesheet">
  <title>{$title}</title>
</svelte:head>

<Router url={url} primary={false}>
  <Page>
    <Route path="donation/:donation_id" component="{DonationPage}" />
    <Route path="donator/:donator_id" component="{DonatorPage}" />
    <Route path="youtube/:channel_id" component="{YoutubeChannelPage}" />
    <Route path="youtube/:channel_id/withdraw" component="{WithdrawPage}" />
    <Route path="youtube/:channel_id/link" component="{YoutubeLinkPage}" />
    <Route path="donate/:channel_id" component="{DonatePage}" />
    <Route path="fulfill/:donator_id" component="{FulfillPage}" />
    <Route path="prove/youtube" component={YoutubeProvePage} />
    <Route path="login" component={LoginPage} />
    <Route path="main" component={Main} />
    <Route path="/" component={Landing} />
    <Route path="/test" component={Test} />
  </Page>
</Router>

<style>
:global(body) {
  background-color: #F7F9FF;
  font-weight: 400;
  color: #000000;
  margin: 0;
}
:global(div#app) {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
</style>
