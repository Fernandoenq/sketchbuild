export default [
  {
    files: ["frontend/src/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        fetch: "readonly",
        FormData: "readonly",
        Date: "readonly",
        Math: "readonly",
        Number: "readonly",
        String: "readonly",
        Array: "readonly",
        Object: "readonly",
        Map: "readonly",
        Set: "readonly",
        Promise: "readonly",
        Float32Array: "readonly",
        Uint32Array: "readonly",
        Uint8Array: "readonly",
        requestAnimationFrame: "readonly",
        cancelAnimationFrame: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        prompt: "readonly",
        Blob: "readonly",
        URL: "readonly",
        THREE: "readonly"
      }
    },
    rules: {
      "no-undef": "error"
    }
  }
];


