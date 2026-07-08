**DOM-based XSS** – DOM-based Cross-Site Scripting (DOM XSS) is a **type of XSS attack where malicious code executes entirely inside the user’s browser when client-side JavaScript unsafely modifies the page’s DOM (Document Object Model)**, without the server returning the malicious script.

#### How it Works?

1. Website JavaScript reads data from the browser (URL, hash, input, etc.)
2. It inserts that data into the page unsafely
3. Malicious JavaScript executes in the browser

Typical unsafe pattern:

```
URL → JavaScript → DOM → Script executes
```

This happens **client-side only**.

**Example:**

Unsafe behavior:

```
Website reads:location.searchThen inserts into:innerHTML
```

Attacker puts malicious content in the URL → browser executes it.

#### How to prevent it?

- Use [[Input Validation]]
- Prefer `textContent` instead of `innerHTML`
- Avoid dangerous functions like `eval()`
- Sanitize HTML before rendering
- Use [[Content Security Policy (CSP)]]

#### Simple analogy

DOM-based XSS is like:

giving a visitor a marker and accidentally letting them rewrite instructions posted inside the building after they enter.

In short, DOM-based XSS is a client-side web security vulnerability where JavaScript modifies the browser’s DOM using untrusted input, causing malicious scripts to execute directly in the user’s browser.