<script>
  import Button from "../../frontend/src/lib/Button.svelte";
  import Arrow2 from "./Arrow2.svelte";
	import {createEventDispatcher} from 'svelte';
  import {getStatic} from "./common.js";

  export let element;
  export let amount;

	const dispatch = createEventDispatcher();
</script>

<div bind:this={element} class="comment">
  <div class="flex-row inner-comment">
    <img width=26 height=26 src={getStatic("success.png")} alt="success">
    <div class="flex-column gap-3">
      <p class="text-align-center margin-0">Donated {amount} sats</p>
      <Button on:click={() => dispatch("comment")} --height=24px --font-size=12px --padding=0 --width=161px >
        <div class="flex-row align-center button">
          <span>Post a comment</span>
          <Arrow2 />
        </div>
      </Button>
    </div>
  </div>
</div>

<style>
.comment {
  padding: 1px;
  position: absolute;
  top: 100%;
  font-size: 12px;
  background-image: linear-gradient(to right, #F9F03E 0%, #9DEDA2 100%);
  border-radius: 8px;
  z-index: 1000; /* YouTube author icons has z-index:300 for some reason */
}
.inner-comment {
  padding: 7px 28px 8px 9px;
  gap: 9px;
  background: white;
  border-radius: 7px;
}
.button {
  padding-left: 15px;
}
</style>
