<script>
  import YoutubeChannel from "$lib/YoutubeChannel.svelte";
  import ChannelLogo from "$lib/ChannelLogo.svelte";
  import Button from "$lib/Button.svelte";

  export let youtube_channels;
</script>

<ul>
  {#each youtube_channels as channel}
  <li>
    <ChannelLogo url={channel.thumbnail_url} size=40px />
    <div class="channel-name">
      <YoutubeChannel linkto=withdraw channel={channel} />
    </div>
    <div class="withdraw-button">
      <Button link="/youtube/{channel.id}">Withdraw</Button>
    </div>
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 17px;
  padding: 16px;
  height: 72px;
  background: linear-gradient(90deg, rgba(157, 237, 162, 0.15) 0%, rgba(157, 237, 162, 0) 100%);
  border-radius: 8px;
}
.withdraw-button {
  width: 136px;
  height: 44px;
  justify-self: end;
}
.channel-name {
  width: 100%;
}
</style>
