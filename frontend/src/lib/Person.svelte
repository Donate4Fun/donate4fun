<script>
  import GithubBrand from "svelte-awesome-icons/GithubBrand.svelte";
  import LinkedinBrand from "svelte-awesome-icons/LinkedinBrand.svelte";
  import TwitterBrand from "svelte-awesome-icons/TwitterBrand.svelte";
  import TelegramBrand from "svelte-awesome-icons/TelegramBrand.svelte";
  import DribbbleBrand from "svelte-awesome-icons/DribbbleBrand.svelte";

  export let photo;
  export let name;
  export let title;
  export let linkedin = null;
  export let twitter = null;
  export let github = null;
  export let telegram = null;
  export let dribbble = null;
</script>

<div class="person">
  <img alt={name} src={photo}>
  <div class="description">
    <p style="grid-row: name;" class="name">{name}</p>
    <p style="grid-row: title;" class="title">{title}</p>
    <div style="grid-row: social;" class="flex-row gap-24">
      {#if linkedin}
        <a target=_blank href={linkedin}><LinkedinBrand size=24 color="#0A66C2" /></a>
      {/if}
      {#if github}
        <a target=_blank href={github}><GithubBrand size=24 color="black" /></a>
      {/if}
      {#if dribbble}
        <a target=_blank href={dribbble}><DribbbleBrand size=24 color="black" /></a>
      {/if}
      {#if twitter}
        <a target=_blank href={twitter}><TwitterBrand size=24 color="#1DA1F2" /></a>
      {/if}
      {#if telegram}
        <a target=_blank href={telegram}><TelegramBrand size=24 color="#1DA1F2" /></a>
      {/if}
    </div>
  </div>
</div>

<style>
.person {
  display: flex;
  align-items: end;
  gap: 20px;
}
img {
  width: 116px;
  height: 116px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
}
.name {
  font-weight: 600;
  font-size: 16px;
  line-height: 22px;
}
.title {
  font-weight: 400;
  font-size: 12px;
  line-height: 16px;
  text-transform: uppercase;
}
.description {
  display: grid;
  grid-template-rows: [name] 22px 8px [title] 16px 24px [social] 24px; 
}
</style>
