<script>
  import { onMount, tick } from "svelte";
  import { useResolve, useLocation, useNavigate, link } from "svelte-navigator";
  import LandingYoutuber from "$lib/LandingYoutuber.svelte";
  import Button from "$lib/Button.svelte";
  import Section from "$lib/Section.svelte";
  import LandingSection from "$lib/LandingSection.svelte";
  import LandingSteps from "$lib/LandingSteps.svelte";
  import Person from "$lib/Person.svelte";
  import Input from "$lib/Input.svelte";
  import ExtensionPopup from "$lib/ExtensionPopup.svelte";
  import FAQ from "$lib/FAQ.svelte";
  import api from "$lib/api.js";
  import { analytics } from "$lib/analytics.js";
  import title from "$lib/title.js";

  let youtubers = [];
  let email;
  let emailAdded = null;
  let extensionPopupShown = false;
  const resolve = useResolve();
  const location = useLocation();
  let navigate = useNavigate();

  function showExtensionPopup() {
    analytics.track("show-extension-popup-from-landing");
    extensionPopupShown = true;
  }

  async function loadRecentDonatees() {
    youtubers = await api.get("donatee/recently-donated");
  }

  async function submitEmail() {
    const response = await api.post("subscribe-email", {email: email});
    emailAdded = response !== null;
  }
  // For #hashtag navigation - thnx to https://github.com/mefechoel/svelte-navigator/issues/39#issuecomment-851433750
  onMount(() => {
    // Don't use the `$` shorthand for store subscription here, since
    // we only want to run this when the app has mounted, not
    // when the component is created
    const unsubscribe = location.subscribe(async (newLocation) => {
      // If there's no hash, we don't need to scroll anywhere
      if (!newLocation.hash) return;
      // We need to wait for svelte to update the dom before atempting to
      // scroll to a specific element
      await tick();
      // Get the element referenced by the fragment. `location.hash`
      // always starts with `#` when a hash exists, so we already have a
      // valid id selector
      const fragmentReference = document.querySelector(newLocation.hash);
      // If the fragment does not reference an element, we can ignore it
      if (!fragmentReference) return;
      fragmentReference.scrollIntoView({block: "center"});
      // Set a tabindex, so the element can be focused
      if (!fragmentReference.hasAttribute('tabindex')) {
        fragmentReference.setAttribute('tabindex', '-1');
        // Remove the tabindex on blur to prevent weird jumpy browser behaviour
        fragmentReference.addEventListener(
          'blur',
          () => fragmentReference.removeAttribute('tabindex'),
          { once: true },
        );
      }
      fragmentReference.focus();
      // By setting location.hash explictly, we ensure :target
      // selectors in CSS will work as expected
      window.location.hash = newLocation.hash;
    });
    return unsubscribe;
  });
  onMount(title.clear);
</script>

<ExtensionPopup bind:show={extensionPopupShown} />
<div class="landing">
  <section class="header" id="main">
    <h1>One click instant donations with <span class="gradient-light">Bitcoin ⚡ Lightning on Youtube. <span class="gradient-dark">Near zero fees.</span></span></h1>
    <div class="annotation">
      🔥Instant delivery and withdraw with Lightning network. No KYC.🔥
    </div>
    <div class="desktop-only" on:click={showExtensionPopup}>
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
    <LandingSteps />
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
        <div class="faq-header">
          <h2 class="gradient-dark">FAQ</h2>
          <a href="/faq" use:link>View all<img src="/static/arrow-right.svg" alt="arrow-right"></a>
        </div>
        <div class="faq"><FAQ /></div>
      </div>
    </Section>
    <Section>
      <div class="half-box" id="team">
        <h2 class="gradient-dark">Team</h2>
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
            <path d="M 2,2 22,2 22,22 M 22,2 2,22" stroke="#004EE7" stroke-width="3" stroke-linejoin="round"/>
          </svg>
        </sup>
      </h1>
    </a>
  </section>
</div>

<style>
.landing {
  display: flex;
  flex-direction: column;
  gap: 88px;
  padding-top: 140px;
}
section {
  display: flex;
  flex-direction: column;
  align-items: center;
}
h1, h2 {
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
  .half-box {
    width: 560px;
    padding: 40px;
    min-height: 535px;
  }
  .faq {
    margin: 0 -40px;
  }
}
@media (max-width: 640px) {
  .header video {
    display: none;
  }
  .half-box {
    width: 100%;
    padding: 28px;
  }
  .faq {
    margin: 0 -28px;
  }
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
.half-box {
  display: flex;
  flex-direction: column;
}
.half-box h2 {
  line-height: 49px;
  text-align: left;
}
h2 {
  font-size: 40px;
}
.faq-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.faq-header a {
  display: flex;
  gap: 6px;
}
.faq :global(details:nth-child(n+5)) {
  display: none;
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
  font-size: 64px !important;
  line-height: 56px;
  transition: all 0.2s ease;
}
.roadmap:hover {
  background: linear-gradient(270.06deg, #004EE7 0.04%, #A863FF 99.94%), linear-gradient(90deg, #F9F03E 0%, #9DEDA2 100%), linear-gradient(90deg, #FF4B4B 0%, #DC24A9 100%);
  -webkit-background-clip: text;
  background-clip: text;
}
</style>
