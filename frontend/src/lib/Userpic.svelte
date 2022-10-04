<script>
  import {link} from "svelte-navigator";
  import {webOrigin} from "../lib/utils.js";

  export let user;
</script>

<a href="{$webOrigin}/donator/{user.id}" use:link {...$$restProps}><img src="{user.avatar_url}" alt="user logo"></a>

<style>
a {
  display: flex;
}
img {
  width: var(--width);
}
</style>
