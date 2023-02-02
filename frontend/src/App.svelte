<script>
  import { onMount, onDestroy } from "svelte";
  import { Router, Link, Route, globalHistory } from "svelte-navigator";

  import Page from "$lib/Page.svelte";
  import title from "$lib/title.js";
  import { analytics } from "$lib/analytics.js";
  import { notify } from "$lib/notifications.js";
  import { ApiError, errorToText } from "$lib/api.js";
  import { cLog } from "$lib/log.js";
  import { decodeJwt } from "$lib/jwt.js";
  import DonatorPage from "./routes/DonatorPage.svelte";
  import DonatePage from "./routes/DonatePage.svelte";
  import FulfillPage from "./routes/FulfillPage.svelte";
  import DonationPage from "./routes/DonationPage.svelte";
  import YoutubeChannelPage from "./routes/YoutubeChannelPage.svelte";
  import YoutubeChannelOwnerPage from "./routes/YoutubeChannelOwnerPage.svelte";
  import WithdrawPage from "./routes/WithdrawPage.svelte";
  import YoutubeLinkPage from "./routes/YoutubeLinkPage.svelte";
  import TwitterAccountPage from "./routes/TwitterAccountPage.svelte";
  import TwitterAccountOwnerPage from "./routes/TwitterAccountOwnerPage.svelte";
  import GithubUserPage from "./routes/GithubUserPage.svelte";
  import GithubUserOwnerPage from "./routes/GithubUserOwnerPage.svelte";
  import LoginPage from "./routes/LoginPage.svelte";
  import Test from "./routes/Test.svelte";
  import Landing from "./routes/Landing.svelte";
  import TermsPage from "./routes/Terms.svelte";
  import NotFoundPage from "./routes/NotFoundPage.svelte";
  import PrivacyPage from "./routes/Privacy.svelte";
  import Welcome from "./routes/Welcome.svelte";
  import FAQPage from "./routes/FAQ.svelte";
  import InstallWebLNWalletPage from "./routes/InstallWebLNWalletPage.svelte";
  import SigninPage from "./routes/SigninPage.svelte";
  import SettingsPage from "./routes/SettingsPage.svelte";
  import LatestDonationsPage from "./routes/LatestDonationsPage.svelte";
  import TopUnclaimedDonateesPage from "./routes/TopUnclaimedDonateesPage.svelte";

  const url = "";
  let simpleHeader = false;

  window.history.pushState = new Proxy(window.history.pushState, {
    apply (target, thisArg, argumentsList) {
      cLog("apply", target);
      Reflect.apply(target, thisArg, argumentsList);
      scrollTo(0,0);
    }
  });

  onMount(async () => {
    analytics.page();
    const url = new URL(window.location.href);
    const toastsToken = url.searchParams.get('toasts');
    if (toastsToken !== null) {
      url.searchParams.delete('toasts');
      const toasts = await decodeJwt(toastsToken);
      for (const toast of toasts.toasts)
        notify(toast.title, toast.message, toast.icon, { showFooter: false });
      window.history.replaceState({}, null, url);
    }
  });

  function onNavigate(event) {
    cLog("onNavigate", event);
    analytics.page();
    simpleHeader = event.location.pathname.match(/\/donation\/.*/)
  }
  const unlisten = globalHistory.listen(onNavigate);
	onDestroy(unlisten);

  window.onerror = (event, source, lineno, colno, error) => {
    cLog("onError", event, source, lineno, colno, error);
    if (event.reason instanceof ApiError)
      notify("Server Error", errorToText(event.reason.response), "error");
    else
      notify("Unhandled error", event.reason, "error");
  };
  window.addEventListener("unhandledrejection", (event) => {
    cLog("onUnhandledRejection", event);
    if (event.reason instanceof ApiError)
      notify("Server Error", errorToText(event.reason.response), "error");
    else
      notify("Unhandled rejection", event.reason, "error");
  });
</script>

<svelte:head>
  <title>{$title}</title>
</svelte:head>

<Router url={url} primary={false}>
  <Page simpleHeader={simpleHeader}>
    <Route path="youtube/*">
      <Route path=":channel_id" component="{YoutubeChannelPage}" />
      <Route path=":channel_id/link" component="{YoutubeLinkPage}" />
      <Route path=":channel_id/owner" component="{YoutubeChannelOwnerPage}" />
    </Route>
    <Route path="twitter/*">
      <Route path=":account_id" component="{TwitterAccountPage}"/>
      <Route path=":account_id/owner" component="{TwitterAccountOwnerPage}"/>
    </Route>
    <Route path="github/*">
      <Route path=":user_id" component="{GithubUserPage}"/>
      <Route path=":user_id/owner" component="{GithubUserOwnerPage}"/>
    </Route>
    <Route path="me/withdraw" component="{WithdrawPage}" />
    <Route path="donation/:donation_id" component="{DonationPage}" />
    <Route path="donator/:donator_id" component="{DonatorPage}" />
    <Route path="donate/:channel_id" component="{DonatePage}" />
    <Route path="fulfill/:donator_id" component="{FulfillPage}" />
    <Route path="login" component={LoginPage} />
    <Route path="test" component={Test} />
    <Route path="terms"><TermsPage /></Route>
    <Route path="privacy"><PrivacyPage /></Route>
    <Route path="welcome"><Welcome /></Route>
    <Route path="faq"><FAQPage /></Route>
    <Route path="install-webln-wallet"><InstallWebLNWalletPage /></Route>
    <Route path="signin"><SigninPage /></Route>
    <Route path="settings"><SettingsPage /></Route>
    <Route path="latest"><LatestDonationsPage /></Route>
    <Route path="top-unclaimed"><TopUnclaimedDonateesPage /></Route>
    <Route path="/"><Landing /></Route>
    <Route component={NotFoundPage}></Route>
  </Page>
</Router>
