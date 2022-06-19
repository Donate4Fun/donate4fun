<script>
  import { createEventDispatcher } from 'svelte';
  import Button from "../lib/Button.svelte";
  import Section from "../lib/Section.svelte";
  import Infobox from "../lib/Infobox.svelte";
  import Loading from "../lib/Loading.svelte";
  import Amount from "../lib/Amount.svelte";
  import { me } from "../lib/session.js";
  import { copy, partial } from "../lib/utils.js";

  const dispatch = createEventDispatcher();

  export let amount;
  export let claimed_at;
  export let donator;
  export let donator_id;
  export let r_hash;
  export let id;
  export let trigger;
  export let paid_at;
  export let created_at;
  export let youtube_channel;

  let message = `
      I’ve donated ${amount} satoshi for you.
      Thank you for great content you make.
      Claim your donation at <b>https://donate4.fun/claim/${youtube_channel.channel_id}</b>
  `;
</script>

<Section class="donation-section">
{#await me.init()}
  <Loading/>
{:then}
  <img class="youtube_channel_thumbnail" src="{youtube_channel.thumbnail_url}" alt="channel logo">
  <div class="header">Donation of <Amount amount={amount}/> sent to <span class="channel-title">{youtube_channel.title}</span>.</div>
  {#if !claimed_at }
    {#if $me.donator.id === donator_id}
    <Infobox>Copy and share the message with the link or just tell Ninja to receive the donation here at «Donate4Fun»</Infobox>
    <div contenteditable class="message" bind:innerHTML={message}></div>
    <Button on:click="{copy(message)}">Copy and Share</Button>
    <Button on:click="{partial(dispatch, "close")}">Back</Button>
    {/if}
  {:else}
    Claimed at {claimed_at}
  {/if}
{/await}
</Section>

<style>
:global(.donation-section) {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 30em;
  gap: 1em;
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
.channel-title {
  color: #004EE7;
}
.message {
  border-radius: 8px;
  background-color: #F8F8F8;
  border-width: 1px;
  padding: 1em;
}
:global(.donation-section button) {
  width: 20em;
}
</style>
