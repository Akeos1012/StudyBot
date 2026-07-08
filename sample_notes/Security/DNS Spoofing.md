**DNS Spoofing ** – A **cyberattack where an attacker sends fake DNS responses to trick a user or system into connecting to the wrong IP address, usually a malicious website**.

#### How it works?

- You request a website (e.g. bank.com)
- Your system asks DNS for the correct [[IP Address]]
- The attacker intercepts or fakes the response
- You get a wrong IP address
- You are redirected to a fake site

**Example:**

Normal:

```
bank.com → 203.0.113.10 (real bank server)
```

Spoofed:

```
bank.com → 10.10.10.10 (fake phishing site)
```

#### What attackers can do?

- steal login credentials
- redirect users to phishing pages
- inject malware
- intercept [[Network]] traffic
- impersonate trusted websites

#### How it is prevented?

- [[DNS Security]] (DNSSEC validation)
- encrypted DNS (DoH / DoT)
- secure [[Network]] routing
- authentication of DNS responses
- firewall and intrusion detection systems

#### Simple analogy

DNS Spoofing is like:

someone pretending to be a trusted GPS system and deliberately giving you the wrong directions to a fake destination.


In short, DNS Spoofing is a cyberattack where fake DNS responses are used to redirect users to malicious websites by providing incorrect IP address mappings for legitimate domain names.