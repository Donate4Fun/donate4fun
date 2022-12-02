<script>
  import Userpic from "$lib/Userpic.svelte";
  import {link} from "svelte-navigator";

  export let user;
  export let ellipsis = false;
</script>

<a href="/donator/{user.id}" use:link {...$$restProps}>
  <Userpic user={user} --width=2em />
  <span class:ellipsis>{user.name}</span>
</a>

<style>
a {
  display: flex;
  align-items: center;
  gap: var(--gap, 1em);
  min-width: 0;
}
</style>
