<script>
  import { derived } from "svelte/store";

  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import WhiteButton from "$lib/WhiteButton.svelte";
  import AmountButton from "$lib/AmountButton.svelte";
  import LandingButton from "$lib/LandingButton.svelte";
  import ServiceLinkButton from "$lib/ServiceLinkButton.svelte";
  import HoldButton from "$lib/HoldButton.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Loader from "$lib/Loader.svelte";
  import SocialUserpic from "$lib/SocialUserpic.svelte";
  import SocialSigninButton from "$lib/SocialSigninButton.svelte";
  import { notify } from "$lib/notifications.js";
  import { sleep } from "$lib/utils.js";
  import { get, ApiError, api } from "$lib/api.js";
  import { cLog, cError } from "$lib/log.js";
  import { syncMe as me } from "$lib/session.js";

  import * as jose from "jose";

  async function testJwt() {
    const JWKS = jose.createRemoteJWKSet(new URL(`${window.location.origin}/.well-known/jwks.json`));
    const token = 'eyJhbGciOiJFUzI1NiJ9.eyJhYWEiOiJhYWEiLCJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjUxNzMiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjUxNzMiLCJzdWIiOiJnZyJ9.xDZJ0KH4i1SjNQ1qG1sgN5PFB9cs7QVyD_kmA-MBgKUkkcmNy_4PBJCyyAgJNtK3hX1W0YxmSpbHM47xDsCvrA';
    const res = await jose.jwtVerify(token, JWKS);
    cLog("jose", res);
  }

  let i = 0;
  let resolve;
  let disabled = false;
  let socialProvider = 'twitter';

  const itemsStore = derived(me, ($me, set) => {
    cLog("itemsStore", socialProvider, $me);
    if (socialProvider === null || $me === null)
      return;
    const ws = api.subscribe(`donator:${$me.donator.id}`);
    ws.on("notification", async (notification) => {
      if (notification.status === 'OK') {
        set(await api.get(`social/${socialProvider}/linked`));
      }
    });
    ws.on("close", () => {
      cLog("close", socialProvider);
    });
    ws.on("open", () => {
      cLog("open", socialProvider);
    });
    ws.on("error", () => {
      cLog("error", socialProvider);
    });
    (async () => {
      try {
        cLog("before wsReady", socialProvider);
        await ws.ready();
        cLog("wsready", socialProvider);
        set(await api.get(`social/${socialProvider}/linked`));
        cLog("store.set", socialProvider);
      } catch (err) {
        cError("Failed to load linked items", err);
        if (err.target instanceof WebSocket && err.type === 'error')
          notify("Network error", "WebSocket error in linked items store", "error");
      }
    })();
    return () => {
      cLog("close ws", socialProvider);
      ws.close();
    };
  }, []);
</script>

<Spinner />
<Loader />
<Loader --size=4em />
<Loader --size=8em />
<div>
  {#if $itemsStore}
    <span>{$itemsStore}</span>
  {/if}
  <SocialUserpic social="twitter" src="https://pbs.twimg.com/profile_images/1574697734535348224/dzdW0yfs_x96.png" />
  <SocialUserpic social="youtube" src="https://pbs.twimg.com/profile_images/1574697734535348224/dzdW0yfs_x96.png" />
  <SocialSigninButton colored idp=twitter apiPath="twitter/oauth">Colored Twitter OAuth2</SocialSigninButton>
  <SocialSigninButton idp=youtube>Uncolored youtube sign in</SocialSigninButton>
  <SocialSigninButton idp=twitter apiPath="twitter/oauth1">Twitter OAuth1</SocialSigninButton>
  <HoldButton --height=48px on:click={async () => {notify("done"); await sleep(1000);}}>Hold me</HoldButton>
  <a href="https://twitter.com" target="_self">Twitter</a>
  <a href="https://m.twitter.com" target="_self">Mob Twitter</a>
  <a href={'#'} on:click|preventDefault={() => window.open('https://twitter.com/', '_blank')}>Twitter Wnd</a>
  <Button on:click={async () => await sleep(1000)}>Sleep 1000</Button>
  <Button on:click={() => {notify(`default title ${i}`, 'default message', 'info', {timeout: 15000}); i++;}}>notify</Button>
  <Button on:click={() => {return new Promise((resolve_) => {resolve = resolve_;})}}>Start Loader</Button>
  <Button on:click={() => {resolve && resolve();}}>Stop Loader</Button>
  <Button on:click={() => {throw new Error("some error");}}>Throw error</Button>
  <Button on:click={async () => {throw new ApiError({data: {error: "some error data"}});}}>Throw ApiError</Button>
  <Button on:click={async () => { get("nonexistent"); }}>Fetch API - 400</Button>
  <Button on:click={() => disabled = !disabled}>Toggle disabled</Button>
  <WhiteButton {disabled}>White</WhiteButton>
  <WhiteButton --background-image="linear-gradient(blue, red)" {disabled}>White custom bg</WhiteButton>
  <Button {disabled} --width=200px>Primary</Button>
  <LandingButton {disabled}>Landing</LandingButton>
  <GrayButton {disabled}>Gray</GrayButton>
  <AmountButton {disabled} selected>Amount Selected</AmountButton>
  <AmountButton {disabled}>Amount Dimmed</AmountButton>
  <ServiceLinkButton link="https://google.com" {disabled}>Service Link</ServiceLinkButton>
</div>

<style>
div {
  width: 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>
