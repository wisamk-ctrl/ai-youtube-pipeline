[Section: Opening]

[Face]
OpenAI's Sam Altman is in the UAE, and ADNOC and G42 are signing an AI deal with OpenAI.

[Visual: stock code on screen with security scan animation, glowing blue]
That same week, OpenAI is launching a model built specifically for security vulnerabilities.

[Visual: stock processor chip under light, macro animation]
And NVIDIA says every execution step an AI agent takes goes through the CPU.

[Pause]

[Face]
So what does this mean for companies here?

[Pause]

Hi everyone, welcome to This Week in AI. I'm Wissam.

[Pause 2s]

[Section: ADNOC and G42 with OpenAI]

[Corner: stock digital globe with glowing network lines over the Gulf region]
Let's start in the Gulf.

[Visual: source 5d7e2da583]
According to Reuters, ADNOC and G42 signed a deal with OpenAI.

[Visual: stock world map network animation connecting two glowing points]
And the deal came while Sam Altman was travelling to the UAE.

[Visual: source 7d5edd20c1]
Yahoo Finance described the agreement as a multi-year AI initiative.

[Visual: source 611db20fcc]
Another report put a number on it, and said it's a deal for

[Pause]

[Visual: number 5 years | Deal length]
5 years.

[On-Screen Text: Multi-year / 5-year AI deal]

[Visual: stock abstract data flow, glowing particles on dark background]
OK, so what exactly is in the deal? What's it worth? What are the projects?

[Pause]

Those details aren't in the sources we have, so we're not going to guess.

[Corner: stock digital globe network map, blue glow]
Why does this matter for us here in the region?

[Pause]

Because OpenAI is tying itself, for years, to ADNOC and G42 in Abu Dhabi.

[Corner: stock server racks in a data centre, blue light]
That means companies in the Gulf could get OpenAI's capabilities through local partners like G42.

And that affects vendor choice, procurement, and the whole data sovereignty conversation.

[Face]
Picture yourself as the CTO of a Jordanian company that works with clients in the Gulf.

What's the first question you'd ask?

[Pause]

Most likely: where will the data be stored, and who can access it?

[Pause 2s]

[Section: HUMAIN and Sovereign AI]

[Face]
OK, and what about Saudi Arabia?

[Pause]

[Visual: source 9300b70a91]
According to AI Magazine, HUMAIN is linked to a sovereign AI initiative worth

[Pause]

[Visual: number $2.6 billion | Sovereign AI initiative]
$2.6 billion.

[On-Screen Text: $2.6bn]

[Visual: stock digital network connecting nodes, animation, blue and gold light]
And the initiative is tied to the Public Investment Fund, PIF, and Aramco.

[Visual: stock two glowing data networks converging on a digital globe]
So in both the UAE and Saudi Arabia, energy companies and sovereign funds are now at the heart of AI deals.

[Corner: stock server racks in a data centre, blue light]
Why does it matter?

[Pause]

For Saudi companies and government suppliers, this could mean local options for compute and for models.

[Corner: stock digital shield protecting data inside a glowing map outline]
Especially for organisations that prefer to keep their data inside the country.

And that's important when a company is planning where its data will be stored.

[Pause 2s]

[Section: GPT-6 Cyber]

[Corner: stock circuit board macro with moving light pulses]
Now let's change pace a little, from deals to cybersecurity.

[Visual: source 53c56afbaf]
OpenAI announced GPT-6 Cyber.

[Visual: stock terminal code on screen, red warning flagged then turning green]
It's a model specialised in finding exploitable security vulnerabilities, and it also develops fixes for them.

[Visual: title Authorized scope]
And the point the company emphasised: the model is trained to stay within authorized scope.

[On-Screen Text: "trained to stay within authorized scope"]

[Visual: stock neural network animation, glowing nodes]
So it's an advanced model, but built for one domain, not a general model that does everything.

[Corner: stock cybersecurity digital shield animation, blue glow]
Why does this matter here?

[Pause]

Security teams at banks, telecoms and government bodies could end up with an AI colleague that hunts for vulnerabilities and develops the fix.

[Corner: stock code on screen with scrolling lines, dark theme]
And this is where defining "authorized scope" itself becomes a governance and legal job, not just a technical one.

[Face]
But there's a big question in front of CISOs and regulators:

[Pause]

How do you make sure a tool that can reach a vulnerability stays within its limits?

[Pause 2s]

[Section: Coding Agents in the Cloud]

[Corner: stock glowing cloud computing network animation]
Now, on to agents.

Agents are starting to move off the developer's laptop and become infrastructure, with rules and governance.

[Visual: source 5beddb2a54]
AWS published how to run Claude Code as a remote agent on Bedrock AgentCore.

[Visual: stock cloud servers with isolated glowing container boxes, animation]
Each task runs in an isolated session inside your own AWS account, and sends you back a pull request on GitHub to review and merge.

[Visual: stock laptop closing while data flows to the cloud, animation]
So you give it the task, close your laptop, and come back to find the result.

[Face]
OK, and security?

[Pause]

[Visual: stock digital padlock and key animation, data flow]
There are temporary IAM permissions, private connectivity through PrivateLink, and audit logs in CloudTrail.

[Visual: stock digital globe with regional network map, glowing nodes]
There are also inference profiles by geographic region, so the data stays where it is.

[Visual: stock data encryption animation, glowing binary streams]
And AWS says Bedrock doesn't use your content to train models, and doesn't share it with the model providers.

[Visual: stock server racks in a data centre, blue light]
There's also a new inference engine called Mantle, designed so that AWS operators have no technical way to access your data.

And you decide whether requests and outputs are stored or not.

[Visual: stock digital shield with checkmark, animation, blue light]
The platform is in scope for certifications like SOC and ISO, and you can use it in a GDPR-compliant way.

[Pause]

[Visual: source b8bac355d6]
In another post, AWS explained how AgentCore Gateway works with Okta Cross App Access.

[Visual: stock network of many connected nodes, animation, glowing]
The idea is simple: one agent and two tools is one thing; hundreds of agents and thousands of tools is something else.

[Visual: stock code on screen with scattered rule files]
If every tool writes its permission rules into its own code, those rules drift over time, and you can't audit them from one place.

[Visual: title One policy at the gateway]
So the solution they propose: Cedar policies in one place, at the gateway, with deny by default unless there's a permission.

[Visual: source 3e5d35744d]
And there's a ServiceNow integration that keeps the user's own identity, not the app's, through on-behalf-of token exchange.

[Visual: stock digital identity verification animation, fingerprint glow]
Why does that matter?

[Pause]

Because without it, the request arrives under the app's name, so the audit trail is lost and the user's own permissions get bypassed.

[Visual: source 8491ebd6e6]
And Anthropic released Claude Code version 2.1.317.

[Visual: stock analytics dashboard animation with glowing charts]
It has a cost-reporting API: per developer, per day, or per identity group.

So management can see agent spending by developer or by team.

[Visual: stock terminal code on screen, dark theme, warning prompt]
There are also new fields in OTel metrics, and a warning when a scheduled task picks up connectors you didn't ask for.

And it asks you before a tool sends your account email over the network.

[Corner: stock digital globe network map, blue glow]
Why does this matter here?

[Pause]

[Corner: title Four questions before agents]
There are four questions any CTO in Jordan or the Gulf usually asks before running agents:

[Pause]

[Corner: stock server racks in a data centre, blue light]
Where's the data? Who audits? Whose name is the agent acting under? And how much does it cost?

[Pause]

[Corner: stock cloud billing dashboard animation, glowing numbers]
This week's releases try to answer all four, including billing through your existing AWS account, with no per-user license.

[Corner: stock digital shield and padlock over network, animation]
So banks and government bodies, with their strict audit requirements, could have clearer answers when they negotiate with vendors.

[Pause 2s]

[Section: NVIDIA's Vera CPU]

[Corner: source e8438a23db]
Over in the chip world, NVIDIA says agents don't run only on GPUs.

[Visual: stock circuit board macro with light pulses between two chips]
An agent moves between reasoning on the GPU and execution on the CPU, things like searching, writing code and testing it.

[Visual: stock data centre with glowing power lines, animation]
NVIDIA says data centres are limited by power, so the question is: how much work do you get out of every watt?

[Pause]

In a comparison for a data centre with

[Pause]

[Visual: number 100 MW | Data centre capacity]
100 megawatts, NVIDIA says the Vera CPU runs

[Pause]

[Visual: number 1.6x | Agents per watt vs the fastest x86 CPU]
1.6 times the agents per watt, compared with the fastest x86 CPU.

[Visual: stock animated bar chart data visualization, glowing bars]
And compared with the most power-efficient x86 CPU, it says agents run twice as fast.

Perplexity ran agentic coding tasks

[Pause]

[Visual: number 1.5x | Faster on agentic coding tasks]
1.5 times faster than on traditional CPUs, and plans to use Vera in an upcoming production system.

[Visual: stock grid of isolated container cubes lighting up, animation]
And Daytona launched 1,000 isolated sandboxes in

[Pause]

[Visual: number 10.8 seconds | To launch 1,000 sandboxes]
10.8 seconds, versus 88.4 seconds on x86.

[On-Screen Text: 10.8s vs 88.4s — 1,000 sandboxes]

[Visual: stock memory chip macro, glowing circuits]
On memory, NVIDIA says pressure on GPU memory is growing, supply is shrinking, and prices are going up.

And from Blackwell Ultra to Vera Rubin, HBM capacity per GPU went up by about

[Pause]

[Visual: number 3% | Increase in HBM capacity per GPU]
just 3%.

Meanwhile, agent performance per dollar went up as much as

[Pause]

[Visual: number 30x | Agent performance per dollar]
30 times, on a benchmark called SemiAnalysis AgentX.

[Face]
And keep in mind, all these numbers come from NVIDIA and its partners, not from an independent source.

[Corner: stock data centre aisle with server racks, blue light]
Why does it matter?

[Pause]

People building data centres in the Gulf are planning with limited power, so agents per watt and memory efficiency directly affect capacity and cost.

[Corner: stock memory chip macro, glowing circuits]
And as memory gets more expensive, the question becomes: how much work do you get out of the same memory, not just how much memory you have?

[Pause]

[Corner: stock digital globe network map, blue glow]
And these numbers will come up in any conversation with vendors.

[Pause 2s]

[Section: This Week's Radar]

[Corner: stock radar screen sweep animation, glowing green]
This week's radar.

[Visual: source 9f1346ce69]
China's Tencent is back on the radar, and this week it was the subject of

[Pause]

[Visual: number 6 reports | Independent reports on Tencent this week]
6 independent reports, about a benchmark and about a launch.

[Visual: title Hy4 on OpenRouter]
And the concrete signal: its Hy4 model is now available on OpenRouter.

[Corner: stock code on screen API request, dark theme]
Why does it matter?

[Pause]

Teams in the region can now try another Chinese model through an API they already know, and that widens the options.

[Face]
The performance numbers still aren't clear to us, so let's keep watching.

[Pause 2s]

[Section: Quick Hits]

[Face]
And quickly, a few stories before we wrap up.

[Visual: source 195f4627fb]
TII in the UAE and Naval Group have partnered to develop autonomous underwater technologies.

[Visual: source bcfd72dabc]
The Abu Dhabi Arabic Language Centre and NYU Abu Dhabi launched the BAREC 2.0 project, a corpus for evaluating how readable Arabic text is.

[Visual: source e2baf2e1c3]
OpenAI released Codex update 0.167.0, with improvements to the agent command centre and a new setup method for Google Cloud Vertex AI.

[Visual: source 9cb1868256]
And in Saudi Arabia, SDAIA and the General Authority for Media Regulation held an "AI for Impact" event for more than

[Pause]

[Visual: number 250 | Content creators at AI for Impact]
250 content creators.

[Pause 2s]

[Section: Wrap-up]

[Face]
The bottom line: the Gulf is locking in long-term AI partnerships, and agents are getting closer to being infrastructure with rules.

[Corner: stock glowing digital globe with network connections, night]
What do you think? Who's going to benefit most from these partnerships?

[Pause]

[Face]
Subscribe to the channel and tell us what you think in the comments.

Thanks for watching, take care.
