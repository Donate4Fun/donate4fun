<script>
  import { link } from "svelte-navigator";
  import Thumbnail from "$lib/Thumbnail.svelte";

  export let user;
  export let externalLink = false;
  export let showHandle = false;
  export let imagePlacement = 'before';
  export let target = "";

  $: pageLink = externalLink ? `https://github.com/${user.login}` : `/github/${user.id}`;
  $: imageUrl = user.avatar_url.replace('_normal', '_x96');
</script>

<a use:link target={externalLink ? "_blank" : target} href={pageLink} class="container">
  {#if imagePlacement === 'before'}
    <Thumbnail url={imageUrl} />
  {/if}
  <span class="name ellipsis">{user.name}</span>
  {#if showHandle}
    <span class="handle">{user.login}</span>
  {/if}
  {#if imagePlacement === 'after'}
    <Thumbnail url={imageUrl} />
  {/if}
</a>

<style>
.container {
  display: flex;
  align-items: center;
  gap: var(--gap, 0.4em);
  min-width: 0;
}
.handle {
  opacity: 50%;
}
</style>
