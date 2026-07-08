
**Cross-Site Request Forgery** – (CSRF) A **web security attack where a malicious site tricks a logged-in user’s browser into sending unauthorized requests to another website where the user is already authenticated**.

#### How it works?

- You log in to a trusted site (e.g., bank)
- Your browser keeps you logged in (cookies/session)
- You visit a malicious site
- That site silently sends a request to the trusted site
- The trusted site thinks _you_ made the request
#### Key conditions for CSRF

- User is already logged in
- Browser automatically sends cookies/session
- Target site does not verify request origin properly
#### How it is prevented?

- [[CSRF Token]] (unique request verification code)
- [[SameSite Cookie]] policy
- [[Authentication]] checks on every request
- [[Referer Header]] validation
- [[Web Security]] frameworks

In short, Cross-Site Request Forgery (CSRF) is a web security attack where a malicious site tricks a logged-in user’s browser into sending unauthorized requests to a trusted website without the user’s intention.