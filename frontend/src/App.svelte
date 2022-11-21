<script>
  import { onMount, onDestroy } from "svelte";
  import { Router, Link, Route, globalHistory } from "svelte-navigator";

  import Page from "$lib/Page.svelte";
  import title from "$lib/title.js";
  import { analytics } from "$lib/analytics.js";
  import { notify } from "$lib/notifications.js";
  import { ApiError, errorToText } from "$lib/api.js";
  import Main from "./routes/Main.svelte";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import FulfillPage from "./routes/FulfillPage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";
  import YoutubeChannelOwnerPage from "./routes/YoutubeChannelOwnerPage.svelte";
  import WithdrawPage from "./routes/WithdrawPage.svelte";
  import YoutubeLinkPage from "./routes/YoutubeLinkPage.svelte";
  import YoutubeProvePage from "./routes/YoutubeProvePage.svelte";
  import TwitterProvePage from "./routes/TwitterProvePage.svelte";
  import TwitterAccountPage from "./routes/TwitterAccountPage.svelte";
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
      console.log("apply", target);
      Reflect.apply(target, thisArg, argumentsList);
      scrollTo(0,0);
    }
  });

  onMount(analytics.page);

  function onNavigate(event) {
    console.log("onNavigate", event);
    analytics.page();
  }
  const unlisten = globalHistory.listen(onNavigate);
	onDestroy(unlisten);

  window.onerror = (event, source, lineno, colno, error) => {
    console.log("onError", event, source, lineno, colno, error);
    if (event.reason instanceof ApiError)
      notify("Server Error", errorToText(event.reason.response), "error");
    else
      notify("Unhandled error", event.reason, "error");
  };
  window.addEventListener("unhandledrejection", (event) => {
    console.log("onUnhandledRejection", event);
    if (event.reason instanceof ApiError)
      notify("Server Error", errorToText(event.reason.response), "error");
    else
      notify("Unhandled error", event.reason, "error");
  });
</script>

<svelte:head>
  <title>{$title}</title>
</svelte:head>

<Router url={url} primary={false}>
  <Page>
    <Route path="youtube/*">
      <Route path="prove" component={YoutubeProvePage} />
      <Route path=":channel_id" component="{YoutubeChannelPage}" />
      <Route path=":channel_id/link" component="{YoutubeLinkPage}" />
      <Route path=":channel_id/owner" component="{YoutubeChannelOwnerPage}" />
    </Route>
    <Route path="twitter/*">
      <Route path="prove" component={TwitterProvePage} />
      <Route path=":account_id" component="{TwitterAccountPage}"/>
    </Route>
    <Route path="me/withdraw" component="{WithdrawPage}" />
    <Route path="donation/:donation_id" component="{DonationPage}" />
    <Route path="donator/:donator_id" component="{DonatorPage}" />
    <Route path="donate/:channel_id" component="{DonatePage}" />
    <Route path="fulfill/:donator_id" component="{FulfillPage}" />
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
