<script>
  import { link } from "svelte-navigator";

  export let account;
  export let externalLink = false;
  export let showHandle = false;
  export let imagePlacement = 'before';

  $: pageLink = externalLink ? `https://twitter.com/${account.handle}` : `/twitter/${account.id}`;
  $: imageUrl = account.profile_image_url.replace('_normal', '_x96');
</script>

<a use:link target={externalLink ? "_blank" : ""} href={pageLink} class="container">
  {#if imagePlacement === 'before'}
    <img class="avatar" alt=avatar src={imageUrl} />
  {/if}
  <span class="name ellipsis">{account.name}</span>
  {#if showHandle}
    <span class="handle">@{account.handle}</span>
  {/if}
  {#if imagePlacement === 'after'}
    <img class="avatar" alt=avatar src={imageUrl} />
  {/if}
</a>

<style>
.container {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
  min-width: 0;
}
.avatar {
  width: var(--image-size, 32px);
  height: var(--image-size, 32px);
  border-radius: 100%;
}
.handle {
  opacity: 50%;
}
</style>
