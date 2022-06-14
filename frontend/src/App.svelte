<script>
  import { Router, Link, Route } from "svelte-navigator";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";

  const url = "";
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,700,900" rel="stylesheet">
</svelte:head>

<Router url={url}>
  <div>
    <Route path="donation/:donation_id" component="{DonationPage}" />
    <Route path="youtube-channel/:channel_id" component="{YoutubeChannelPage}" />
    <Route path="donator/:donator_id" component="{DonatorPage}" />
    <Route path="/"><Main /></Route>
  </div>
</Router>

<style>
:global(body) {
  background: #F7F9FF;
  font-family: Inter;
  font-weight: 400;
  color: #000000;
  padding: 20px;
}
</style>
