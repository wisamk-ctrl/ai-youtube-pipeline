# W45 — English reading script (your voice)

A faithful translation of the Arabic read: same stories, same figures, same sources, nothing added.

## Opening (selfie if you want your face on screen, or voice only)

OpenAI's Sam Altman is in the UAE, and ADNOC and G42 are signing an AI deal with OpenAI. The same week, OpenAI launches a model built for security vulnerabilities. And Nvidia says every step an AI agent executes runs through the CPU.

So what does all this mean for businesses in our region?

Welcome to AI Week. I'm Wissam.

## Main read (voice only)

Let's start in the Gulf. According to Reuters, ADNOC and G42 have signed a deal with OpenAI, and it landed while Sam Altman was visiting the UAE. Yahoo Finance described it as a multi-year AI initiative. Another report put a length on it: five years.

So what exactly is in the deal? Its value? Its projects?

Those details aren't in our sources, so we won't guess. Why does it matter here in the region?

Because OpenAI is tying itself, for years, to ADNOC and G42 in Abu Dhabi. That means companies in the Gulf may get OpenAI's capabilities through local partners like G42. And that shapes vendor choice, procurement, and the whole data-sovereignty conversation. Picture yourself as the CTO of a Jordanian company with clients in the Gulf. What's the first question you'd ask?

Most likely: where will the data be stored, and who can get to it?

And Saudi Arabia?

According to AI Magazine, HUMAIN is linked to a sovereign AI initiative worth 2.6 billion dollars. The initiative is tied to the Public Investment Fund, PIF, and to Aramco. So in both the UAE and Saudi Arabia, energy companies and sovereign funds are now at the centre of AI deals. Why does that matter?

For Saudi companies, and for anyone supplying the government, it could mean local options for compute and for models. Especially for organisations that want their data to stay inside the country. And that matters whenever a company plans where its data will live.

Now a change of pace: from deals to cybersecurity. OpenAI announced GPT-6 Cyber. It's a model specialised in finding exploitable security vulnerabilities, and in developing fixes for them. The point the company stressed: the model is trained to stay within its authorised scope. So it's an advanced model, but built for one domain, not a general model that does everything. Why does that matter to us?

Security teams at banks, telecoms and government bodies could get an AI colleague that hunts for vulnerabilities and develops the fix. And defining that "authorised scope" becomes a governance and legal job, not just a technical one. But there's a big question in front of CISOs and regulators:

How do you make sure a tool that can reach a vulnerability stays within its limits?

Now to agents. Agents are moving off the developer's laptop and becoming infrastructure, with rules and governance. AWS published how to run Claude Code as a remote agent on Bedrock AgentCore. Each task runs in an isolated session inside your own AWS account, and comes back as a pull request on GitHub for you to review and merge. So you hand it the task, close the laptop, and come back to the result. And security?

There are temporary IAM permissions, a private connection through PrivateLink, and audit logs in CloudTrail. There are also regional inference profiles, so the data stays where it is. AWS says Bedrock doesn't use your content to train models, and doesn't share it with the model providers. And there's a new inference engine called Mantle, designed so that AWS operators have no technical way to reach your data. You decide whether prompts and responses are stored or not. The platform is in scope for certifications such as SOC and ISO, and you can use it in a GDPR-compliant way.

In a second post, AWS explained how AgentCore Gateway works with Okta Cross App Access. The idea is simple: one agent and two tools is one thing; hundreds of agents and thousands of tools is something else. If every tool writes its permission rules into its own code, those rules drift over time, and you can't audit them from one place. Their answer: Cedar policies in one place, at the gateway, denied by default unless there's a permission. And there's a ServiceNow integration that keeps the user's own identity, not the application's, through on-behalf-of token exchange. Why does that matter?

Because without it, the request arrives under the application's name, the audit trail is lost, and the user's own permissions are bypassed. Anthropic also shipped a new release of Claude Code. It has a cost-report API: per developer, per day, or per identity group. So management can see agent spend by developer or by team. There are new fields in its OTel metrics, a warning when a scheduled task picks up connectors you didn't ask for, and it now asks you before a tool sends your account email over the network. Why does that matter here?

There are four questions almost any CTO in Jordan or the Gulf asks before running agents:

Where's the data? Who audits it? Whose identity is the agent acting under? And what does it cost?

This week's releases try to answer all four, including billing through your existing AWS account, with no per-user licence. So banks and government bodies with strict audit requirements may have clearer answers when they negotiate with vendors.

In chips, Nvidia says agents don't run only on GPUs. An agent moves between thinking on the GPU and executing on the CPU: searching, writing code, and testing it. And Nvidia says data centres are limited by power, so the question is: how much work do you get out of every watt?

Comparing a 100-megawatt data centre, Nvidia says its Vera CPU runs 1.6 times as many agents per watt as the fastest x86 processor. And against the most power-efficient x86 processor, it says agent speed is double. Perplexity ran agentic coding tasks 1.5 times faster than on traditional processors, and plans to use Vera in an upcoming production system. And Daytona spun up a thousand isolated sandboxes in 10.8 seconds, against 88.4 seconds on x86.

On memory, Nvidia says the pressure on GPU memory is rising, supply is shrinking, and prices are going up. From Blackwell Ultra to Vera Rubin, HBM capacity per GPU grew by only about 3 percent. Meanwhile, agent performance per dollar grew up to 30 times, on a benchmark called SemiAnalysis AgentX. And note: all of these numbers come from Nvidia and its partners, not from an independent source. Why does it matter?

People building data centres in the Gulf are planning around limited power, so agents per watt and memory efficiency feed straight into capacity and cost. And as memory gets more expensive, the question becomes: how much work do you get out of the same memory, not just how much memory do you have?

Expect these numbers to come up in every vendor conversation.

This week's radar. China's Tencent is back on the radar: this week it was the subject of six independent reports, on a benchmark and on a launch. The concrete signal: its Hy4 model is now on OpenRouter. Why does it matter?

Teams in the region can now try another Chinese model through an API they already know, and that widens the options. The performance numbers aren't clear to us yet, so let's keep watching.

And quickly, a few items before we wrap up. The UAE's TII and Naval Group have partnered to develop autonomous underwater technologies. The Abu Dhabi Arabic Language Centre and NYU Abu Dhabi launched BAREC 2.0, a corpus for assessing how readable Arabic text is. OpenAI shipped a new Codex update, with improvements to its agent command centre and a new setup path for Google Cloud Vertex AI. And in Saudi Arabia, SDAIA and the General Authority for Media Regulation held "AI for Impact" for more than 250 content creators.

## Closing (selfie or voice)

The takeaway: the Gulf is locking in long-term AI partnerships, and agents are becoming infrastructure with rules. Now over to you: who do you think stands to gain most from these partnerships?

Subscribe to the channel, and tell us what you think in the comments. Thanks for watching.
