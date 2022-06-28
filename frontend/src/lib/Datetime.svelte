<script>
  import dateFormat, { masks } from "dateformat";

  export let dt;

  $: dtString = (() => {
    if (dt !== null) {
      return dateFormat(dt, "DDDD H:M")
    } else {
      return "";
    }
  })();
</script>

{dtString}
