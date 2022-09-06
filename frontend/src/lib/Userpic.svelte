<script>
  import {link} from "svelte-navigator";

  export let user;
</script>

<a href="/donator/{user.id}" use:link {...$$restProps}><img src="{user.avatar_url}" alt="user logo"></a>

<style>
a {
  display: flex;
}
img {
  width: 3em;
}
</style>
