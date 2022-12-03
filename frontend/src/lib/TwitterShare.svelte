<script>
  import WhiteButton from "$lib/WhiteButton.svelte";

  export let text;
  let shareUrl;

  $: {
    shareUrl = new URL('https://twitter.com/intent/tweet');
    shareUrl.searchParams.append('text', text);
    shareUrl.searchParams.append('url', location.href);
    shareUrl.searchParams.append('via', 'donate4_fun');
  }
</script>

<WhiteButton link={shareUrl} target="_blank">
  <div class="main">
    <img alt=youtube src="/static/twitter.svg" width=20>
    <span>Share</span>
  </div>
</WhiteButton>

<style>
.main {
  display: flex;
  gap: 8px;
}
</style>
