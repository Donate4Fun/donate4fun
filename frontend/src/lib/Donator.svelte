<script>
  import Userpic from "$lib/Userpic.svelte";
  import {link} from "svelte-navigator";

  export let user;
  export let ellipsis = false;
  export let target = "";
</script>

<a href="/donator/{user.id}" target={target} use:link>
  <div>
    <Userpic user={user} --width=2em />
    <span class:ellipsis>{user.name}</span>
  </div>
</a>

<style>
a {
  min-width: 0;
}
div {
  display: flex;
  align-items: center;
  gap: var(--gap, 1em);
}
</style>
