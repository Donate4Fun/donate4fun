<script>
  import { Router, Link, Route } from "svelte-navigator";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";

  const url = "";
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,500,700,900" rel="stylesheet">
</svelte:head>

<Router url={url}>
  <Route path="donation/:donation_id" component="{DonationPage}" />
  <Route path="youtube-channel/:channel_id" component="{YoutubeChannelPage}" />
  <Route path="donator/:donator_id" component="{DonatorPage}" />
  <Route path="donate/:channel_id" component="{DonatePage}" />
  <Route path="/"><Main /></Route>
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
:global(div#app > *) {
  padding: 2em;
}
:global(a) {
  color: #004EE7;
  text-decoration: none;
}
</style>
