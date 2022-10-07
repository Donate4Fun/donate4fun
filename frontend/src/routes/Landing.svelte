<script>
  import { useResolve } from "svelte-navigator";
  import LandingStep from "$lib/LandingStep.svelte";
  import LandingYoutuber from "$lib/LandingYoutuber.svelte";
  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import LandingSection from "$lib/LandingSection.svelte";
  import Person from "$lib/Person.svelte";
  import Input from "$lib/Input.svelte";
  import ExtensionPopup from "$lib/ExtensionPopup.svelte";
  import WalletPopup from "$lib/WalletPopup.svelte";
  import FAQ from "$lib/FAQ.svelte";
  import api from "$lib/api.js";
  import { isWeblnPresent, isExtensionPresent } from "$lib/utils.js";

  let youtubers = [];
  let email;
  let emailAdded = null;
  let showExtensionPopup = false;
  let showWalletPopup = false;
  const resolve = useResolve();

  async function loadRecentDonatees() {
    youtubers = await api.get("donatee/recently-donated");
  }

  async function submitEmail() {
    const response = await api.post("subscribe-email", {email: email});
    emailAdded = response !== null;
  }
</script>

<svelte:head>
  <title>Donate4.Fun • Donate anyone on YouTube with Bitcoin Lightning</title>
</svelte:head>

<div class="page">
  <ExtensionPopup bind:show={showExtensionPopup} />
  <WalletPopup bind:show={showWalletPopup} />
  <section class="header" id="main">
    <h1>One click instant donations with <span class="gradient-light">Bitcoin ⚡ Lightning on Youtube. <span class="gradient-dark">Near zero fees.</span></span></h1>
    <div class="annotation">
      🔥Instant delivery and withdraw with Lightning network. No KYC.🔥
    </div>
    <div class="desktop-only" on:click={() => showExtensionPopup = true}>
      <Button --width=300px>Get extension</Button>
    </div>
    <form on:submit|preventDefault={submitEmail} class="mobile-only flex-column gap-18 text-align-center">
      Currently we support only desktop browsers.
      <Input bind:value={email} placeholder="Add your email" />
      <Button type=submit>
        {#if emailAdded === null}
          Notify me when app is ready
        {:else if emailAdded === true}
          You've been subscribed!
        {:else if emailAdded === false}
          Already subscribed!
        {/if}
      </Button>
    </form>
    <video autoplay muted loop src="/static/sample.webm" width=640px />
  </section>
  <section id="howto">
    <h1 class="gradient-light">How to donate</h1>
    <content class="steps">
      <div on:click={() => showExtensionPopup = true} class="step narrow">
        <LandingStep number=1 done={isExtensionPresent()}>
          <img slot=image alt="D" src="/static/extensions.svg">
          <div slot=text>
            <p>Get Donate4.Fun</p>
            <p>browser extension</p>
          </div>
        </LandingStep>
      </div>
      <div on:click={() => showWalletPopup = true} class="step narrow">
        <LandingStep number=2 done={isWeblnPresent()}>
          <img slot=image src="/static/wallet.svg" alt="wallet">
          <div slot=text>
            <p>Get a Lightning Wallet</p>
            <p>if you don’t have it yet</p>
            <p>And fulfill with satoshis</p>
          </div>
        </LandingStep>
      </div>
      <a href="https://youtube.com" target=_blank class="step wide">
        <LandingStep number=3>
          <img slot=image alt="browser-extension" src="/static/extension-popup.png" height=188>
          <div slot=text>
            <p>Go to YouTube and click a ⚡ icon under video or open Donate4fun Google Extension to donate</p>
          </div>
        </LandingStep>
      </a>
    </content>
  </section>
  <section id="donatees">
    <h1 class="gradient-dark">Top donated</h1>
    {#await loadRecentDonatees() then}
      <div class="donatees">
        <div class="flex-row gap-20">
          {#each youtubers as youtuber}
            <LandingYoutuber youtuber={youtuber} />
          {/each}
        </div>
      </div>
    {/await}
  </section>
  <section id="claim">
    <img src="/static/coin.png" alt="bitcoin" width=88 height=88>
    <h1 class="gradient-light">Want to get your donations?</h1>
    <Button class="white" --width=300px link={resolve("/prove/youtube")}>Claim here</Button>
  </section>
  <div class="flex-row gap-20 justify-center flex-wrap">
    <Section>
      <div class="half-box">
        <h1 class="gradient-dark">FAQ</h1>
        <FAQ />
      </div>
    </Section>
    <Section>
      <div class="half-box">
        <h1 class="gradient-dark">Team</h1>
        <div class="annotation">
          <p>Passionate founders. Big dreamers.</p>
          <p>Proven builders. Ready to change the game.</p>
        </div>
        <div class="flex-column gap-44">
          <Person
            name="Nikolay Bryskin"
            title="Founder, developer and creator"
            photo="/static/nbryskin.jpeg"
            linkedin="https://linkedin.com/nbryskin"
            twitter="https://twitter.com/nbryskin"
            github="https://github.com/nikicat"
            telegram="https://t.me/nbryskin"
          />
          <Person
            name="Klim Novopashin"
            title="CO-FOUNDER. Product UX/UI designer"
            photo="/static/klim.jpeg"
            linkedin="https://www.linkedin.com/in/klim-nova/"
            twitter="https://twitter.com/Novaklim1"
            telegram="https://t.me/Klim_Nova"
            dribbble="https://dribbble.com/Klim_Nova"
          />
        </div>
      </div>
    </Section>
  </div>
  <section id="roadmap">
    <a href="https://github.com/orgs/Donate4Fun/projects/1" target=_blank>
      <h1 class="gradient-dark roadmap">Roadmap<sup>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 2H22M22 2V22M22 2L2 22" stroke="#004EE7" stroke-width="3" stroke-linejoin="round"/>
          </svg>
        </sup>
      </h1>
    </a>
  </section>
</div>

<style>
.page {
  display: flex;
  flex-direction: column;
  gap: 88px;
}
:global(body) {
  background-image: url("/static/background-bolt.svg");
  background-repeat: no-repeat;
  background-position: top;
}
section {
  display: flex;
  flex-direction: column;
  align-items: center;
}
h1 {
  font-family: 'Montserrat';
  font-style: normal;
  font-weight: 900;
  text-align: center;
}
@media (max-width: 640px) {
  h1 {
    font-size: 32px;
    line-height: 40px;
  }
  :not(#main) > h1 {
    margin-bottom: 28px;
  }
}
@media (min-width: 641px) {
  h1 {
    line-height: 56px;
  }
  #main > h1 {
    font-size: 44px;
    width: 100%;
    max-width: 700px;
  }
  :not(#main) > h1 {
    font-size: 40px;
    margin-bottom: 28px;
  }
}
.gradient-light {
  background: linear-gradient(89.59deg, #FF9634 27.11%, #DC24A9 92.47%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
.gradient-dark {
  background: linear-gradient(90deg, #FF4B4B 0%, #DC24A9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
@media (min-width: 641px) {
  .step.narrow {
    width: 340px;
  }
  .step.wide {
    width: 426px;
  }
  .half-box {
    width: 560px;
    padding: 40px;
    min-height: 535px;
  }
}
@media (max-width: 640px) {
  .step {
    width: 328px;
  }
  .header video {
    display: none;
  }
  .half-box {
    width: 100%;
    padding: 28px;
  }
}
.step {
  height: 450px;
  color: var(--color);
  font-weight: 500;
  cursor: pointer;
}
.step div {
  text-align: center;
}
.step.wide p {
  max-width: 308px;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 22px;
}
#main .annotation {
  margin-top: 32px;
  margin-bottom: 42px;
  font-weight: 500;
  font-size: 20px;
  line-height: 30px;
  text-align: center;
}
#main video {
  margin-top: 56px;
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 20px;
}
.half-box h1 {
  line-height: 49px;
  text-align: left;
}
.annotation {
  margin-top: 16px;
  margin-bottom: 40px;
}
.donatees {
  width: calc(100vw - 20px); /* page width minus some margin to get rid of horiz scrollbar */
  padding-left: 20px;
}
.donatees div {
  overflow-x: scroll;
  white-space: nowrap;
  padding-bottom: 30px; /* to show shadow */
  -ms-overflow-style: none;  /* hide scroll for Internet Explorer 10+ */
  scrollbar-width: none;  /* hide scroll for Firefox */
}
.donatees div::-webkit-scrollbar {
  display: none;  /* hide scroll for Safari and Chrome */
}
.roadmap {
  text-decoration-line: underline;
  font-size: 64px;
  line-height: 64px;
}
</style>
