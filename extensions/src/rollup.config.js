import svelte from "rollup-plugin-svelte";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import alias from '@rollup/plugin-alias';
import replace from "@rollup/plugin-replace";
import copy from '@guanghechen/rollup-plugin-copy';
import styles from "rollup-plugin-styles";
import path from "path";
import fs from "fs";

const dev = process.env.ROLLUP_WATCH;
const distDir = dev ? "../" : "../dist/";

function serve() {
  let server;

  function toExit() {
    if (server) server.kill(0);
  }

  return {
    writeBundle() {
      if (server) return;
      server = require("child_process").spawn(
        "npm",
        ["run", "start", "--", "--dev"],
        {
          stdio: ["ignore", "inherit", "inherit"],
          shell: true,
        }
      );

      process.on("SIGTERM", toExit);
      process.on("exit", toExit);
    },
  };
}

function makeOutput(browser, options) {
  return {
    sourcemap: dev,
    format: "iife",
    name: "app",
    dir: path.join(distDir, browser, options?.dir || '.'),
    assetFileNames: "[name][extname]",
    footer: options?.footer,
  }
}

function makeConfig(name, options) {
  return {
    input: `${name}.js`,
    output: [
      makeOutput('chrome', options),
      makeOutput('firefox', options),
    ],
    plugins: [
      svelte({
        compilerOptions: {
          dev: dev,
        },
        onwarn: (warning, handler) => {
          // e.g. don't warn on <marquee> elements, cos they're cool
          if (["a11y-click-events-have-key-events", "security-anchor-rel-noreferrer"].includes(warning.code)) return;
          console.log("onwarn", warning.code);

          // let Rollup handle all other warnings normally
          handler(warning);
        },
      }),
      // we'll extract any component CSS out into
      // a separate file - better for performance
      styles({mode: ["extract", `${path.basename(name)}.css`]}),

      // If you have external dependencies installed from
      // npm, you'll most likely need these plugins. In
      // some cases you'll need additional configuration -
      // consult the documentation for details:
      // https://github.com/rollup/plugins/tree/master/packages/commonjs
      resolve({
        browser: true,
        dedupe: ["svelte"],
      }),
      commonjs(),
      alias({
        entries: {
          '$lib': path.resolve(__dirname, '../../frontend/src/lib'),
          '$extlib': path.resolve(__dirname, './lib'),
        },
      }),
      replace({
        "process.env.NODE_ENV": JSON.stringify(process.env.NODE_ENV),
        "import.meta.env.DEV": dev,
        preventAssignment: false,
      }),
      copy({
        targets: [
          { src: `${name}.html`, dest: [distDir + "chrome", distDir + "firefox"] },
        ],
      }),
    ],
    watch: {
      clearScreen: false,
    },
  }
}

function staticFile(filename) {
  return {
    src: `static/${filename}`,
    dest: [distDir + "chrome/static", distDir + "firefox/static"],
  }
}

function manifestFile(src, dest, transform) {
  return {
    src: src,
    dest: path.dirname(dest),
    rename: "manifest.json",
    transform: (contents, filename) => JSON.stringify(transform(JSON.parse(contents))),
  }
}

function getVersion() {
  return JSON.parse(fs.readFileSync("package.json")).version;
}

function patchChromeManifest(json) {
  if (dev) {
    // Add localhost to allow cookie access
    json.host_permissions = [...json.host_permissions, '*://localhost/'];
    json.web_accessible_resources[1].matches = [...json.web_accessible_resources[1].matches, 'http://localhost:3000/*'];
    json.content_scripts[1].matches = [...json.content_scripts[1].matches, 'http://localhost:3000/*'];
  }
  json.version = getVersion();
  return json;
}

function patchFirefoxManifest(json) {
  if (dev) {
    // Use *:// instead of http:// because firefox does not allow to get secure cookies for http://localhost
    json.permissions = [...json.permissions, '*://localhost/*'];
    json.content_scripts[1].matches = [...json.content_scripts[1].matches, 'http://localhost/*'];
  }
  json.version = getVersion();
  return json;
}

export default [
  makeConfig('options'),
  makeConfig('popup'),
  makeConfig('window'),
  makeConfig('background'),
  makeConfig('youtube/contentscript', {dir: 'youtube', footer: "app;"}), // we need to return pormise from contentscript.js to wait in scripting.executeScript
  makeConfig('twitter/contentscript', {dir: 'twitter', footer: "app;"}),
  makeConfig('donate4.fun/contentscript', {dir: 'donate4.fun'}),
  makeConfig('webln'),
  makeConfig('globalobj'),
  {
    input: "./empty.js",
    treeshake: false,
    output: [
      makeOutput('chrome'),
      makeOutput('firefox'),
    ],
    plugins: [
      resolve({
        browser: true,
      }),
      copy({
        targets: [
          staticFile("D.svg"),
          staticFile("Inter.var.woff2"),
          staticFile("global.css"),
          staticFile("defaults.css"),
          staticFile("D-*.png"),
          staticFile("lottie-*.json"),
          staticFile("youtube.svg"),
          staticFile("twitter.svg"),
          staticFile("checkbox.svg"),
          staticFile("loader.svg"),
          { src: "background.html", dest: distDir + "firefox" },
          manifestFile("manifest-firefox.json", distDir + "firefox/manifest.json", patchFirefoxManifest),
          manifestFile("manifest-chrome.json", distDir + "chrome/manifest.json", patchChromeManifest),
        ],
        verbose: true,
      }),
    ],
  },
];
