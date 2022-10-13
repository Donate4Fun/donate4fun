const cLog = process.env.DEV ? console.log.bind(console, '[⚡₿] %s') : () => {};
const cInfo = console.log.bind(console, '[⚡₿] %s');

export default cLog;
export {
  cLog,
  cInfo,
}
