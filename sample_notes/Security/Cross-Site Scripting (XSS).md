**Cross-Site Scripting** – (XSS) a **web security vulnerability where an attacker injects malicious scripts (usually JavaScript) into a trusted website, which then runs in the browser of other users**.

#### How it works?

1. Attacker finds a way to input code into a website
2. The website stores or displays it without filtering
3. Other users load the page
4. The malicious script runs in their browser

#### How it is prevented?

- [[Input Validation]]
- [[Output Encoding]]
- [[Content Security Policy (CSP)]]
- [[Escaping Special Characters]]
- Secure [[Web Application Security]] practices

**Example:**

A comment section:

```
Great post! <script>alert("Hacked")</script>
```

**If the site doesn’t filter input:**

- every visitor runs the script
- attacker can steal cookies or session data

___
### Types of XSS

- [[Stored XSS]] 
- [[Reflected XSS]] 
- [[DOM-based XSS]] 

In short, Cross-Site Scripting (XSS) is a web security vulnerability where attackers inject malicious scripts into trusted websites, which are then executed in the browsers of other users.