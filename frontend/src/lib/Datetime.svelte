<script>
  import dateFormat, { masks } from "dateformat";

  export let dt;

  $: dtString = (() => {
    if (dt !== null) {
      return dateFormat(dt, "DDDD HH:MM")
    } else {
      return "";
    }
  })();
</script>

{dtString}
