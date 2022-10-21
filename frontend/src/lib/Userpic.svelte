<script>
  import {link} from "svelte-navigator";
  import {webOrigin} from "$lib/utils.js";

  export let user;
</script>

<a href="{$webOrigin}/donator/{user.id}" use:link {...$$restProps}><img title={user.name} src="{user.avatar_url}" alt="user logo"></a>

<style>
a {
  display: flex;
}
img {
  width: var(--width);
  border-radius: 50%;
  transition: all 0.2s ease;
}
img:hover {
  border: 2px solid rgba(46, 108, 255, 0.5);
}
</style>
