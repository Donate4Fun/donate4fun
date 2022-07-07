<script>
  import { Router, Link, Route } from "svelte-navigator";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";
  import WithdrawPage from "./routes/WithdrawPage.svelte";
  import YoutubeLinkPage from "./routes/YoutubeLinkPage.svelte";
  import Test from "./routes/Test.svelte";

  const url = "";
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,500,700,900" rel="stylesheet">
</svelte:head>

<Router url={url}>
  <Route path="donation/:donation_id" component="{DonationPage}" />
  <Route path="donator/:donator_id" component="{DonatorPage}" />
  <Route path="youtube/:channel_id" component="{YoutubeChannelPage}" />
  <Route path="youtube/:channel_id/withdraw" component="{WithdrawPage}" />
  <Route path="youtube/:channel_id/link" component="{YoutubeLinkPage}" />
  <Route path="donate/:channel_id" component="{DonatePage}" />
  <Route path="/" component="{Main}" />
  <Route path="/test" component={Test} />
</Router>

<style>
:global(body) {
  background: #F7F9FF;
  font-family: Inter;
  font-weight: 400;
  color: #000000;
  margin: 0;
}
:global(div#app) {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
:global(a) {
  color: #004EE7;
  text-decoration: none;
  font-weight: 700;
}
:global(*) {
  box-sizing: border-box;
}
</style>
