<script>
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import SocialAccountPage from "$lib/SocialAccountPage.svelte";

  export let channel_id;
</script>

<SocialAccountPage account_id={channel_id} provider="youtube">
  <YoutubeChannel slot="target" let:account={channel} channel={channel} />
</SocialAccountPage>
