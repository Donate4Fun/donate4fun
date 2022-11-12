const cLog =  import.meta.env.DEV ? console.log.bind(console, '[⚡₿] %s') : () => {};
const cInfo = console.log.bind(console, '[⚡₿] %s');
const cError = console.error.bind(console, '[⚡₿] %s');

export default cLog;
export {
  cLog,
  cInfo,
  cError,
}
