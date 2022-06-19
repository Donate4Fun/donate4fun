<script>
  import QRCode from 'qrcode';
  import Spinner from "../lib/Spinner.svelte";

  export let value;
</script>

{#await QRCode.toDataURL(value)}
  <Spinner />
{:then value}
  <img src={value} alt="qrcode" >
{/await}

<style>
img {
  margin: -15px;
  margin-bottom: -20px;
}
</style>
