<script>
  import { onMount } from "svelte";
  import { Router, Link, Route } from "svelte-navigator";
  import Page from "$lib/Page.svelte";
  import title from "$lib/title.js";
  import { analytics } from "$lib/analytics.js";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import FulfillPage from "./routes/FulfillPage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";
  import WithdrawPage from "./routes/WithdrawPage.svelte";
  import YoutubeLinkPage from "./routes/YoutubeLinkPage.svelte";
  import YoutubeProvePage from "./routes/YoutubeProvePage.svelte";
  import TwitterProvePage from "./routes/TwitterProvePage.svelte";
  import TwitterAuthorPage from "./routes/TwitterAuthorPage.svelte";
  import LoginPage from "./routes/LoginPage.svelte";
  import Test from "./routes/Test.svelte";
  import Landing from "./routes/Landing.svelte";
  import TermsPage from "./routes/Terms.svelte";
  import NotFoundPage from "./routes/NotFoundPage.svelte";
  import PrivacyPage from "./routes/Privacy.svelte";
  import Welcome from "./routes/Welcome.svelte";
  import FAQPage from "./routes/FAQ.svelte";
  import InstallWebLNWalletPage from "./routes/InstallWebLNWalletPage.svelte";

  const url = "";

  window.history.pushState = new Proxy(window.history.pushState, {
    apply (target, thisArg, argumentsList) {
      Reflect.apply(target, thisArg, argumentsList);
      scrollTo(0,0);
      analytics.page();
    }
  });

  onMount(analytics.page);
</script>

<svelte:head>
  <title>{$title}</title>
</svelte:head>

<Router url={url} primary={false}>
  <Page>
    <Route path="donation/:donation_id" component="{DonationPage}" />
    <Route path="donator/:donator_id" component="{DonatorPage}" />
    <Route path="youtube/:channel_id" component="{YoutubeChannelPage}" />
    <Route path="youtube/:channel_id/withdraw" component="{WithdrawPage}" />
    <Route path="youtube/:channel_id/link" component="{YoutubeLinkPage}" />
    <Route path="twitter/:account_id" component="{TwitterAuthorPage}"/>
    <Route path="donate/:channel_id" component="{DonatePage}" />
    <Route path="fulfill/:donator_id" component="{FulfillPage}" />
    <Route path="prove/youtube" component={YoutubeProvePage} />
    <Route path="prove/twitter" component={TwitterProvePage} />
    <Route path="login" component={LoginPage} />
    <Route path="main" component={Main} />
    <Route path="test" component={Test} />
    <Route path="terms"><TermsPage /></Route>
    <Route path="privacy"><PrivacyPage /></Route>
    <Route path="welcome"><Welcome /></Route>
    <Route path="faq"><FAQPage /></Route>
    <Route path="install-webln-wallet"><InstallWebLNWalletPage /></Route>
    <Route path="/"><Landing /></Route>
    <Route component={NotFoundPage}></Route>
  </Page>
</Router>
