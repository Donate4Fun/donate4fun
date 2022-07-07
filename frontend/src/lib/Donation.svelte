<script>
  import { createEventDispatcher } from 'svelte';
  import Button from "../lib/Button.svelte";
  import Section from "../lib/Section.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import Loading from "../lib/Loading.svelte";
  import Amount from "../lib/Amount.svelte";
  import YoutubeChannel from "../lib/YoutubeChannel.svelte";
  import Editable from "../lib/Editable.svelte";
  import { me } from "../lib/session.js";
  import { copy } from "../lib/utils.js";

  const dispatch = createEventDispatcher();

  export let amount;
  export let claimed_at;
  export let donator_id;
  export let id;
  export let trigger;
  export let paid_at;
  export let created_at;
  export let youtube_channel;

  let message = `Hi! This video is cool! I’ve donated ${amount} sats to you. You can take it here https://donate4.fun/youtube-channel/${youtube_channel.id}`;
</script>

<main>
{#await me.init()}
  <Loading/>
{:then}
  <img class="youtube_channel_thumbnail" src="{youtube_channel.thumbnail_url}" alt="channel logo">
  <div class="header">Donation of <Amount amount={amount}/> sent to <YoutubeChannel {...youtube_channel}/></div>
  {#if !claimed_at }
    {#if $me.donator.id === donator_id}
    <Infobox>Copy and share the message with the link or just tell {youtube_channel.title} to receive the donation here at «Donate4Fun»</Infobox>
    <Editable class=message message={message} />
    <Button on:click={() => copy(message)} class="copy-button">Copy and Share</Button>
    <Button on:click={() => dispatch("close")} class="grey">Back</Button>
    {/if}
  {:else}
    Claimed at {claimed_at}
  {/if}
{/await}
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 44px 84px 40px 84px;
}
main > img {
  margin-bottom: 16px;
}
main > .header {
  margin-bottom: 22px;
}
main > :global(.message) {
  margin-top: 52px;
  margin-bottom: 28px;
}
main > :global(.copy-button) {
  margin-bottom: 20px;
}
.youtube_channel_thumbnail {
  width: 3em;
  height: 3em;
}
.header {
  font-weight: 900;
  font-size: 24px;
  text-align: center;
}
main > :global(button) {
  width: 402px;
  height: 44px;
}
</style>
