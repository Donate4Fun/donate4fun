<script>
  import Option from "./Option.svelte";
  import {worker} from "./common.js";

  let options = [];

  async function save() {
    let values = {};
    for (const option of options) {
      values[option.name] = option.value;
    }
    await worker.saveOptions(values);
  }

  async function load() {
    console.log("loading");
    options = await worker.loadOptions();
    console.log("options", options);
  }
</script>

<main>
  <h1>Settings</h1>
  {#await load() then}
  <div class=options>
    {#each options as option}
      {#if !option.dev}
        <Option on:change={save} bind:option={option} />
      {/if}
    {/each}
  </div>
  <details>
    <summary>Developer options</summary>
    <div class=options>
      {#each options as option}
        {#if option.dev}
          <Option on:change={save} bind:option={option} />
        {/if}
      {/each}
    </div>
  </details>
  {/await}
</main>

<style>
h1 {
  margin: 0;
  font-family: 'Inter';
  font-weight: 700;
  font-size: 24px;
}
main {
  width: 640px;
  padding: 36px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.options {
  color: black;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
