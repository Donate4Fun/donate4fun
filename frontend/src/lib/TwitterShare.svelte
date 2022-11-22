<script>
  import Button from "$lib/Button.svelte";

  export let text;
  let shareUrl;

  $: {
    shareUrl = new URL('https://twitter.com/intent/tweet');
    shareUrl.searchParams.append('text', text);
    shareUrl.searchParams.append('url', location.href);
    shareUrl.searchParams.append('via', 'donate4_fun');
  }
</script>

<Button class="white" link={shareUrl} target="_blank">
  <img alt=youtube src="/static/twitter.svg" width=20>
  Share
</Button>
