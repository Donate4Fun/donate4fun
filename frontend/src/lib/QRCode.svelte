<script>
  import QRCode from 'qrcode';
  import Spinner from "../lib/Spinner.svelte";

  export let value;
  let datauri;

  $: QRCode.toDataURL(value).then((err, url) => { datauri = url });
</script>

{#await QRCode.toDataURL(value)}
<Spinner />
{:then value}
<img src={value} alt="qrcode" >
{/await}
