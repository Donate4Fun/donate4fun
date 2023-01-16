<script>
  import { useNavigate } from "svelte-navigator";
  import { clickDispatcher } from "$lib/utils.js";
  import BaseButton from "$lib/BaseButton.svelte";
  import ColoredBorder from "$lib/ColoredBorder.svelte";
  import { api } from "$lib/api.js";
  import { sleep } from "$lib/utils.js";

  export let idp;  // Identity Provider
  export let width = 'auto';
  export let height = '40px'
  export let border = '1px';
  export let link;
  export let returnTo = '/donator/me';
  export let colored = false;
  export let padding = '0 40px';
  const isMobile = 'ontouchstart' in document.documentElement;
  // WORKAROUND: Twitter OAuth 2.0 doesn't work on Android/iOS
  // See https://twittercommunity.com/t/web-oauth-2-0-is-broken-on-android-if-twitter-app-is-installed/169698/13
  export let apiPath = (isMobile && idp === 'twitter') ? `${idp}/oauth1` : `${idp}/oauth`;

  const navigate = useNavigate();

  async function click() {
    if (link) {
      navigate(link)
    } else {
      const response = await api.get(apiPath, {params: {return_to: returnTo}});
      window.location.assign(response.url);
      await sleep(10000); // to disable button blinking
    }
  }
</script>

<BaseButton
  --border-width={colored ? 0 : border}
  --border-color=#E9E9E9
  --button-background-color=white
  --height={height}
  --width={width}
  padding=0
  on:click={click}
  {...$$restProps}
>
{#if colored}
  <ColoredBorder --background-color="var(--light-color)">
    <div class="inner" style:padding={padding}>
      <img alt="{idp}" src="/static/{idp}.svg">
      <span class="text"><slot /></span>
    </div>
  </ColoredBorder>
{:else}
  <div class=inner style:padding={padding}>
    <img alt="{idp}" src="/static/{idp}.svg">
    <span class="text"><slot /></span>
  </div>
{/if}
</BaseButton>

<style>
.inner {
  display: flex;
  gap: 16px;
  align-items: center;

  font-weight: 700;
  font-size: 16px;
  line-height: 22px;
  letter-spacing: 0.02em;
  width: 100%;
  height: 100%;
}
.inner > img {
  width: 24px;
}
.text {
  margin: 0 auto;
}
</style>
