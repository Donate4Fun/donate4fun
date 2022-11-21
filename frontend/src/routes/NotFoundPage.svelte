<script>
  import { errorToText } from "$lib/api.js";

  export let error;
</script>

<h3>Page not found</h3>
<div>{ errorToText(error.response) }</div>
