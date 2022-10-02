<script>
  import { useResolve } from "svelte-navigator";
  import Page from "$lib/Page.svelte";
  import LandingStep from "$lib/LandingStep.svelte";
  import LandingYoutuber from "$lib/LandingYoutuber.svelte";
  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import Person from "$lib/Person.svelte";
  import Input from "$lib/Input.svelte";
  import api from "$lib/api.js";

  let youtubers = [];
  let email;
  let emailAdded = null;
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

<Page>
  <div class="page">
    <section class="header" id="main">
      <h1>One click instant donations with <span class="gradient-text">Bitcoin ⚡ Lightning on Youtube.</span> <span class="gradient-text-2">Near zero fees.</span></h1>
      <div class="annotation">
        <p>🔥Instant delivery and withdraw with</p>
        <p>Lightning network. No KYC.🔥</p>
      </div>
      <div class="only-desktop">
        <Button --width=300px>
          <img class="browser-logo" alt="chrome logo" src="/static/chrome.png"><span>Get Chrome extension</span>
        </Button>
      </div>
      <form on:submit|preventDefault={submitEmail} class="only-mobile flex-column gap-18">
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
      <header>Easy to donate</header>
      <content class="steps">
        <div class="step narrow">
          <LandingStep number=1>
            <div class="flex-column align-center justify-center">
              <img alt="D" src="/static/D.svg" width=76px>
            </div>
            <div class="text">Get Donate4.Fun Chrome extension</div>
          </LandingStep>
        </div>
        <div class="step narrow">
          <LandingStep number=2>
            <div class="flex-column align-center justify-center">
              <img src="/static/wallet.png" width=103px alt="wallet">
            </div>
            <div class="text">Get a Lightning Wallet if you don’t have it yet</div>
          </LandingStep>
        </div>
        <div class="step wide">
          <LandingStep number=3>
            <div class="video">
              <video autoplay muted loop src="/static/sample.webm" />
            </div>
            <div class="text">Go to YouTube and click a ⚡ icon under video or open Donate4fun Google Extension to donate</div>
          </LandingStep>
        </div>
      </content>
    </section>
    <section id="donatees">
      <header>Top donated</header>
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
    <section>
      <img src="/static/coin.png" alt="bitcoin" width=88 height=88>
      <header>Want to get your donations?</header>
      <Button class="white" --width=300px link={resolve("/prove/youtube")}>Claim here</Button>
    </section>
    <div class="flex-row gap-20 justify-center flex-wrap">
      <Section>
        <div class="half-box">
          <header>FAQ</header>
        </div>
      </Section>
      <Section>
        <div class="half-box">
          <header>Team</header>
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
    <section>
      <a href="https://github.com/orgs/Donate4Fun/projects/1" target=_blank>
        <header class="roadmap">Roadmap<sup>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 2H22M22 2V22M22 2L2 22" stroke="#004EE7" stroke-width="3" stroke-linejoin="round"/>
            </svg>
          </sup>
        </header>
      </a>
    </section>
  </div>
</Page>

<style>
.page {
  display: flex;
  flex-direction: column;
  gap: 88px;
  width: 100vw;
  padding: 0 14px;
}
section {
  display: flex;
  flex-direction: column;
  align-items: center;
}
header {
  background: linear-gradient(89.59deg, #FF9634 27.11%, #DC24A9 92.47%), #000000;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
  font-family: 'Montserrat';
  font-style: normal;
  font-weight: 900;
  font-size: 40px;
  line-height: 56px;
  margin-bottom: 28px;
  text-align: center;
}
h1 {
  font-family: 'Montserrat';
  font-style: normal;
  font-weight: 900;
  font-size: 44px;
  line-height: 56px;
  text-align: center;
  color: #414141;
  width: 100%;
  max-width: 700px;
}
.gradient-text-2 {
  background: linear-gradient(90deg, #FF4B4B 0%, #DC24A9 100%), #414141;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
@media (min-width: 641px) {
  .only-mobile {
    display: none;
  }
  .step.narrow {
    width: 340px;
  }
  .step.wide {
    width: 426px;
  }
  .half-box {
    width: 560px;
  }
}
@media (max-width: 640px) {
  .only-desktop {
    display: none;
  }
  .step {
    width: 328px;
  }
  .header video {
    display: none;
  }
  .half-box {
    width: 100%;
  }
}
.steps {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 22px;
}
.steps .text {
  text-align: center;
  font-weight: 500;
  font-size: 20px;
  line-height: 30px;
}
.steps .video {
  padding: 0 34px 19px;
}
.steps video {
  width: 100%;
}
.header .annotation {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 32px;
  margin-bottom: 42px;
}
.header .annotation p {
  font-weight: 500;
  font-size: 20px;
  line-height: 30px;
}
video {
  box-shadow: 10px 15px 20px rgba(209, 217, 230, 0.15);
  border-radius: 20px;
}
.header video {
  margin-top: 56px;
}
.gradient-text {
  background: linear-gradient(89.59deg, #FF9634 27.11%, #DC24A9 92.47%), #414141;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
.browser-logo {
  margin-right: 12px;
}
.half-box {
  height: 535px;
  padding: 40px;
}
.half-box header {
  line-height: 49px;
  background: linear-gradient(90deg, #FF4B4B 0%, #DC24A9 100%), #000000;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
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
