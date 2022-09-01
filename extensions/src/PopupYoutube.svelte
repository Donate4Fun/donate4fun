<script>
  import { worker, contentScript, browser } from "./common.js";
  import Header from "../../frontend/src/lib/Header.svelte";
  import Button from "../../frontend/src/lib/Button.svelte";

</script>
 
<Header />
<main>
  <Button>100</Button>
  <Button>1000</Button>
  <Button>10000</Button>
  <Button>100000</Button>
</main>

<style>
main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
