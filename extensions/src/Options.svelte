<script>
  import Option from "./Option.svelte";
  import {worker} from "./common.js";

  let options;
  let newKey;

  async function save() {
    let values = {};
    for (const [key, option] of Object.entries(options))
      if (option.type === 'section')
        for (const [subKey, subOption] of Object.entries(option.options))
          values[subKey] = subOption.value;
      else
        values[key] = option.value;
    await worker.saveOptions(values);
  }

  async function load() {
    console.log("loading");
    options = await worker.loadOptions();
    console.log("options", options);
  }
  
  function addNewKey(option) {
    option.options[`${option.prefix}${newKey}`] = {
      type: "text",
    };
    options = options;
  }
</script>

<main>
  <h1>Settings</h1>
  {#await load() then}
  <div class=options>
  {#each Object.values(options) as option}
    {#if option.type === 'section'}
      <details>
        <summary>{option.name}</summary>
        <div class=options>
        {#each Object.entries(option.options) as [subKey, subOption]}
          <Option on:change={save} on:remove={() => delete option.options[subKey]} bind:option={subOption} key={subKey.replace(option.prefix, '')} />
        {/each}
        {#if option.extendable}
          <div class="flex-row">
            <input bind:value={newKey} />
            <button on:click={() => addNewKey(option)}>Add</button>
          </div>
        {/if}
        </div>
      </details>
    {:else}
      <Option on:change={save} bind:option={option} key={option.name} />
    {/if}
  {/each}
  </div>
  {/await}
</main>

<style>
h1 {
  margin: 0;
  font-weight: 700;
  font-size: 24px;
}
main {
  width: 640px;
  padding: 0 36px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
summary {
  margin-bottom: 16px;
  font-size: 16px;
}
.options {
  color: black;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 0 16px;
}
</style>
