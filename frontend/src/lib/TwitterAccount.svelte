<script>
  import { link } from "svelte-navigator";

  export let account;
  export let externalLink = false;

  $: pageLink = externalLink ? `https://twitter.com/${account.handle}` : `/twitter/${account.id}`;
</script>

<a use:link href={pageLink} class="container">
  <img class="avatar" alt=avatar src={account.profile_image_url} />
  <span class="name">{account.name}</span>
  <span class="handle">@{account.handle}</span>
</a>

<style>
.container {
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 100%;
}
.handle {
  opacity: 50%;
}
</style>
