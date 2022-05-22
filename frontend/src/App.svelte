<script>
  import { Router, Link, Route } from "svelte-routing";
  import Main from "./routes/Main.svelte";
  import DonateePage from "./routes/DonateePage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";

  const url = "";
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,700,900" rel="stylesheet">
</svelte:head>

<Router url={url}>
  <div>
    <Route path="donation/:id" component="{DonationPage}" />
    <Route path="donatee/:donatee" component="{DonateePage}" />
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
