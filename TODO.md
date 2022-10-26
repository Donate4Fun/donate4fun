todo:
- add text for investors and vision
- complete google oauth verification
- add more wallets to landing step 2
- revert donations after 3 months of donatee absense
- withdraw from donator balance
- variable donation amount in bolt button
- add analytics to extension

nice to be done:
- test on opera and edge
- extension for safari
- automatic uploads to chrome and mozilla extension stores
- make site with docs
- accept BTC fulfillments (Boltz)
- subscribe to changes using VAPID instead of websockets
- enable loop and pool in lnd
- integrate ramp.network for fiat fulfillments

look-and-feel:
- restyle youtube bolt animation and popup animation
- login page: add confirmation to reset wallet / disconnect
- speed up first donation on a video (dont wait for youtube api)
- https://blaze-slider.dev/ for donations list on landing
- animate landing elements on scroll

bugs:
- add spinner to fulfillment page
- fulfill invoice: 'need help' is not visible on small screens (x800)
- refresh extension popup balance after fulfill

fixed:
- pause toast timer while tab is in background (works only in chrome)
- confetti on welcome page
- nowebln popup: do not show "get webln enabled wallet" if webln is present
- add analytics to extension and web (https://github.com/DavidWells/analytics)
- fulfill invoice: fix invoice text (replace "donate to")
- extension welcome page: second step is not done although webln is present (until you connect site in alby)
- nowebln popup: opens fullscreen on macos - could not fix
- nowebln popup: fix scrollbars
- fulfill from nowebln - can't change amount
- add FAQ items
- add analytics consent
- restyle FAQ
- sections header layout: move down
- website: element paddings on youtuber page
- update screenshots in web stores
- nowebln page: add links how to get satoshis
- extension popup: update balance after donation
- connect wallet page: add "need help" link
- add terms and privacy
- fulfill page: add "need help" link
- withdraw page: add "need help" link
- withdraw: no page update after withdraw from qrcode (sometimes ?)
- backend: update youtube channel name after change
- get more donations: fix link in copy text box
- frontend: donate page doesn't work
- prove youtube: restyle
- prove youtube: remove "no comments found" on initial load
- fulfill page: add links how to get satoshis
- youtube: comment for non-default languages
- landing mobile layout
- login page: page does not change after connect
- qrcode logo
- nowebln popup page: remove header
- in popup after wallet link pubkey does not change
- donate from popup: nowebln page does not open
- fulfill page doesn't work without connected wallet
- landing: restyle "done" steps
- extension popup header on chrome
- youtube: support shorts
- header layout for desktop
- addon: welcome page
- eliminate errors in chrome extension console
- header: fix quick links on mobile
- youtube bolt animation layout
- extension popup chrome fonts
