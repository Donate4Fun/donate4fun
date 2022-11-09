<script>
  import Option from "./Option.svelte";
  import { worker } from "$extlib/common.js";
  import cLog from "$lib/log.js";

  let options;
  let newKey;

  async function save() {
    let values = {};
    for (const [key, option] of Object.entries(options))
      if (option.type === 'section' || option.type === 'extendable')
        for (const [subKey, subOption] of Object.entries(option.options))
          values[subKey] = subOption.value;
      else
        values[key] = option.value;
    cLog("saving options", values);
    await worker.saveOptions(values);
  }

  async function load() {
    options = await worker.loadOptions();
    cLog("options", options);
  }
  
  function addNewKey(option) {
    cLog("addNewKey", option);
    option.options[`${option.prefix}${newKey.toLowerCase()}`] = {
      type: "text",
      description: newKey.toUpperCase(),
    };
    save();
    options = options;
  }

  async function removeSubKey(option, subKey) {
    cLog("removeSubKey", subKey);
    delete option.options[subKey];
    await worker.removeConfig(subKey);
    options = options;
  }
</script>

<main>
  <h1>Settings</h1>
  {#await load() then}
  <div class=options>
  {#each Object.values(options) as option}
    {#if option.type === 'section' || option.type === 'extendable'}
      <details>
        <summary>{option.name}</summary>
        <div class=options>
        {#each Object.entries(option.options) as [subKey, subOption]}
          <Option on:change={save} on:remove={() => removeSubKey(option, subKey)} bind:option={subOption} key={subKey.replace(option.prefix, '')} />
        {/each}
        {#if option.type === 'extendable'}
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
