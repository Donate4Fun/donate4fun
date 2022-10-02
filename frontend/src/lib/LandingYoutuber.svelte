<script>
  import Section from "$lib/Section.svelte";
  import Amount from "$lib/Amount.svelte";
  import { youtube_channel_url } from "$lib/utils.js";

  export let youtuber;
</script>

<Section>
  <div>
    <img alt="youtuber-logo" src={youtuber.thumbnail_url} width=120 height=120>
    <a class="ellipsis" target=_blank href={youtube_channel_url(youtuber.channel_id)}>{youtuber.title}</a>
    <p>Got donated</p>
    <Amount amount={youtuber.balance} />
  </div>
</Section>

<style>
div {
  width: 240px;
  height: 290px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px
}
img {
  border-radius: 100%;
}
a {
  margin: 20px 22px 16px;
  text-align: center;
  width: 100%;
}
p {
  font-weight: 500;
  font-size: 16px;
  line-height: 24px;
}
</style>
