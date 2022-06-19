<script>
  import Userpic from "../lib/Userpic.svelte";
  import {link} from "svelte-navigator";

  export let user;
</script>

<a href="/donator/{user.id}" use:link>
    <Userpic {...user}/>
    {user.name}
</a>

<style>
a {
  display: flex;
  align-items: center;
  gap: 1em;
}
a :global(img) {
  width: 2em;
}
</style>
