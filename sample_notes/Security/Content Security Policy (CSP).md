**Content Security Policy** – (CSP) A **web security mechanism that allows a website to define which sources of content (scripts, images, styles, etc.) are allowed to load and execute in the browser**, helping prevent attacks like XSS.

#### What CSP does?

- Controls which [[JavaScript]] can run on a page
- Restricts loading of external resources
- Blocks unauthorized scripts and styles
- Reduces risk of [[Cross-Site Scripting (XSS)]]
- Improves [[Web Application Security]]

**Example:**

A CSP policy might say:

```
Only allow scripts from:- mywebsite.com- trustedcdn.com
```

So if a hacker tries:

```
<script src="evil-site.com/hack.js"></script>
```

The browser blocks it.

#### What CSP can control?

- [[Scripts]]
- [[Stylesheets]]
- Images
- Fonts
- [[Frames]]
- [[API]] connections (in some cases)

In short, Content Security Policy (CSP) is a web security mechanism that defines and restricts which content sources are allowed to load and execute in a browser, helping prevent attacks like Cross-Site Scripting (XSS).