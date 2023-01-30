<script>
  import TwitterBrand from "svelte-awesome-icons/TwitterBrand.svelte";
  import YoutubeBrand from "svelte-awesome-icons/YoutubeBrand.svelte";
  import GithubBrand from "svelte-awesome-icons/GithubBrand.svelte";

  import YoutubeVideo from "$lib/YoutubeVideo.svelte";
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import TwitterAccount from "$lib/TwitterAccount.svelte";
  import GithubUser from "$lib/GithubUser.svelte";
  import Donator from "$lib/Donator.svelte";

  export let donation;
</script>

<div class="receiver">
  {#if donation.youtube_video}
    <div class="noshrink"><YoutubeBrand height=20 width=24 color=red /></div>
    <YoutubeVideo video={donation.youtube_video} linkto=channel target="blank" --gap=8px />
  {:else if donation.youtube_channel}
    <div class="noshrink"><YoutubeBrand height=20 width=24 color=red /></div>
    <YoutubeChannel channel={donation.youtube_channel} class="ellipsis" linkto=withdraw target="blank" logo --gap=8px />
  {:else if donation.twitter_account}
    <div class="noshrink"><TwitterBrand width=24 color=#2E6CFF /></div>
    <TwitterAccount account={donation.twitter_account} --image-size=24px --gap=8px target="blank" />
  {:else if donation.github_user}
    <div class="noshrink"><GithubBrand width=24 color=black /></div>
    <GithubUser user={donation.github_user} --image-size=24px --gap=8px target="blank" />
  {:else if donation.receiver}
    <div class="noshrink"><img src="/static/D.svg" height=20 width=24 alt="donate4.fun"></div>
    <Donator user={donation.receiver} ellipsis --gap=8px target="blank" />
  {:else}
    to target
  {/if}
</div>

<style>
.receiver {
  display: flex;
  align-items: center;
  gap: 8px;
}
.noshrink {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
</style>
