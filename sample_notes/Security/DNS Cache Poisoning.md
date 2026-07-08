**DNS cache poisoning** – A **cyberattack where fake or corrupted DNS information is inserted into a DNS resolver’s cache, causing it to return incorrect IP addresses and redirect users to malicious websites**.

- A user requests a website (e.g. google.com)
- The DNS resolver looks up the correct [[IP Address]]
- An attacker injects fake DNS data
- The resolver saves the wrong result in its cache
- Future users get redirected to a fake site

**Example:**

Normal:

```
google.com → 142.250.190.14 (real site)
```

Poisoned:

```
google.com → 10.0.0.99 (fake malicious site)
```

#### What attackers can do?

- steal login credentials
- redirect users to [[phishing]] pages
- inject malware downloads
- intercept [[Network]] traffic
- [[impersonate]] real websites

#### How it is prevented? 

- [[DNS Security]] (DNSSEC validation)
- encrypted DNS (DoH / DoT)
- cache validation and expiration rules
- secure DNS servers
- monitoring suspicious Network activity

In short, DNS Cache Poisoning is a cyberattack where false DNS information is stored in a resolver’s cache, causing users to be redirected to malicious websites instead of legitimate ones.