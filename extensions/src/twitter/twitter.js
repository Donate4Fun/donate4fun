export function getCurrentAccountHandle() {
  const prefix = 'UserAvatar-Container-';
  const avatar = document.querySelector(`[data-testid="SideNav_AccountSwitcher_Button"] [data-testid^="${prefix}"]`) 
  return avatar?.dataset.testid.replace(prefix, '');
}

