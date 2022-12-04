<script>
  import Button from "$lib/Button.svelte";
  import GrayButton from "$lib/GrayButton.svelte";
  import WhiteButton from "$lib/WhiteButton.svelte";
  import AmountButton from "$lib/AmountButton.svelte";
  import LandingButton from "$lib/LandingButton.svelte";
  import ServiceLinkButton from "$lib/ServiceLinkButton.svelte";
  import Spinner from "$lib/Spinner.svelte";
  import Loader from "$lib/Loader.svelte";
  import { notify } from "$lib/notifications.js";
  import { sleep } from "$lib/utils.js";
  import { get, ApiError } from "$lib/api.js";

  let i = 0;
  let resolve;
  let disabled = false;
</script>

<Spinner />
<Loader />
<Loader --size=4em />
<Loader --size=8em />
<div>
  <Button on:click={() => {notify(`default title ${i}`, 'default message', 'info', 15000); i++;}}>notify</Button>
  <Button on:click={() => {return new Promise((resolve_) => {resolve = resolve_;})}}>Start Loader</Button>
  <Button on:click={() => {resolve && resolve();}}>Stop Loader</Button>
  <Button on:click={() => {throw new Error("some error");}}>Throw error</Button>
  <Button on:click={async () => {throw new ApiError({data: {error: "some error data"}});}}>Throw ApiError</Button>
  <Button on:click={async () => { get("nonexistent"); }}>Fetch API - 400</Button>
  <Button on:click={() => disabled = !disabled}>Toggle disabled</Button>
  <WhiteButton {disabled}>White</WhiteButton>
  <WhiteButton --background-image="linear-gradient(blue, red)" {disabled}>White custom bg</WhiteButton>
  <Button {disabled} --width=200px>Primary</Button>
  <LandingButton {disabled}>Landing</LandingButton>
  <GrayButton {disabled}>Gray</GrayButton>
  <AmountButton {disabled} selected>Amount Selected</AmountButton>
  <AmountButton {disabled}>Amount Dimmed</AmountButton>
  <ServiceLinkButton link="https://google.com" {disabled}>Service Link</ServiceLinkButton>
</div>

<style>
div {
  width: 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>
