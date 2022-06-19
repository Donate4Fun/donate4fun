<script>
  import {link} from "svelte-navigator";

  export let name;
  export let avatar_url;
  export let id;
</script>

<a href="/donator/{id}" use:link><img src="{avatar_url}" alt="user logo"></a>

<style>
a {
  display: flex;
}
img {
  width: 3em;
  height: 3em;
  margin-left: 1em;
}
</style>
