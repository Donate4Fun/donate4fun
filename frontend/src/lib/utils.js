function copy(content) {
  return () => {
    navigator.clipboard.writeText(content);
    console.log("Copied to clipboard", content);
  }
}

function partial(func, ...args) {
  return () => {
    func(...args);
  }
}

export { copy, partial };
