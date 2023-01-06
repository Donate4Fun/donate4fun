<script>
  import { useNavigate } from "svelte-navigator";
  import { clickDispatcher } from "$lib/utils.js";
  import BaseButton from "$lib/BaseButton.svelte";
  import { api } from "$lib/api.js";
  import { sleep } from "$lib/utils.js";

  export let type;
  export let width = 'auto';
  export let height = '40px'
  export let link;
  export let returnTo;

  const navigate = useNavigate();

  async function click() {
    if (link)
      navigate(link)
    else {
      const response = await api.get(`${type}/oauth`, {params: {return_to: returnTo}});
      window.location.href = response.url;
      await sleep(10000); // to disable button blinking
    }
  }
</script>

<div class=outer>
  <BaseButton
    --padding="0 40px"
    --background-image="linear-gradient(to right, white, white 100%)"
    --border-width=1px
    --border-color=#E9E9E9
    --height={height}
    --width={width}
    on:click={click}
    {...$$restProps}
  >
    <div class=inner>
      <img alt="{type}" src="/static/{type}.svg">
      <span class="text"><slot /></span>
    </div>
  </BaseButton>
</div>

<style>
.outer {
  box-shadow: 10px 15px 25px rgba(209, 217, 230, 0.4);
  display: contents;
}
.inner {
  font-weight: 700;
  font-size: 16px;
  line-height: 22px;
  letter-spacing: 0.02em;
  display: flex;
  gap: 16px;
  width: 100%;
}
.text {
  margin: 0 auto;
}
</style>
