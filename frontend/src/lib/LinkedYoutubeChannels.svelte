<script>
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import ChannelLogo from "../lib/ChannelLogo.svelte";

  export let youtube_channels;
</script>

<ul>
  {#each youtube_channels as channel}
  <li>
    <ChannelLogo url={channel.thumbnail_url} size=40px />
    <YoutubeChannel linkto=withdraw channel={channel} />
  </li>
  {/each}
</ul>

<style>
ul {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 8px;
  padding: 0;
}
li {
  padding: 16px;
  align-items: center;
  display: flex;
  gap: 17px;
  height: 72px;
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
</style>
