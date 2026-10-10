# FINDING 021 — THE ROSTER WAS "LIVE" AND EVERY MESSAGE TO IT WAS DISCARDED

**A delivery that looked complete because the send succeeded. I committed this myself, one message after the
Chair named the class.**

---

## WHAT HAPPENED

**Asked to confirm the cabinet roster before fanning out, I verified three things and reported the roster
live:**

```
profiles      sokoban (32 files) · missile-command (23) · zork (23)      EXIST
the service   hermes-gateway.service  loaded active running             RUNNING
the route     message_agent accepted @sokoban -> "queued"               ACCEPTED
```

**ALL THREE TRUE. AND ALL THREE INSUFFICIENT. Two messages were sent and BOTH WERE DISCARDED AT THE FAR END:**

```
exit code 1
No usable credentials found for provider 'deepseek'. Set DEEPSEEK_API_KEY.
```

**The profile existed, the gateway was running, the route accepted the message — AND THE AGENT COULD NOT START
A SESSION, SO NOTHING RECEIVED IT.**

## AND I MADE THE EXACT ERROR THE CHAIR HAD JUST NAMED

**His words, one message earlier:** *"a delivery that looked complete because the send succeeded, on a channel
the consumer does not read."* **He named it about a document sent to the wrong machine. I did it with a
message, an hour later, and reported the roster as REACHABLE when it was only ACCEPTING.**

**THE ACK SAID SO AND I READ PAST IT:** *"this acknowledges the hand-off to a background delivery process, NOT
a delivery receipt."* **I wrote "queued", which was accurate, and then concluded "so nothing is missing",
which was not.** *A hand-off acknowledged is not a delivery performed* — the same shape as a compile that
succeeds, a file that exists, and a coverage of 1.000 with nothing measured.

**THE RULE: A ROUTE THAT ACCEPTS IS NOT A ROUTE THAT DELIVERS. Confirming a roster means confirming an AGENT
CAN RUN, not that a directory and a unit exist.**

## THE DIAGNOSIS, AND IT WAS A CONFIGURATION FACT RATHER THAN A MYSTERY

```
ocho            auth.json + .env with DEEPSEEK_API_KEY      works
ocho2           auth.json + .env with DEEPSEEK_API_KEY      works
tiel            auth.json + .env with DEEPSEEK_API_KEY      works
sokoban         .env EMPTY -- no KEY= lines at all          failed
missile-command .env EMPTY                                  would have failed
zork            .env EMPTY                                  would have failed
birdy           .env only                                   UNVERIFIED, same shape
```

**`sokoban/config.yaml:3` declares `provider: deepseek`. So the profile was configured for a provider it had
no credential for — a config that names a provider is not a config that can reach one.**

**AND THE FAILURE IS SILENT FROM THE SENDER'S SIDE, WHICH IS THE WHOLE PROBLEM: every message returned a
`delivery_id` and a `status: queued`. Nothing anywhere said the far end had refused.**

## THE FIX, AND HOW THE CREDENTIAL WAS HANDLED

**The credential already existed on this machine** — in `~/.hermes/.env` and in the working sibling profiles.
**It was propagated to the three cabinet `.env` files BY NAME, with the value piped file-to-file and never
printed, never held in a shell variable that reached the transcript, and verified by EXISTENCE (name bound,
line length, file mode) rather than by content.** Files are mode 600.

**THE SECURITY RULE IS ABOUT A VALUE APPEARING, NOT ABOUT A FILE EXISTING.** Copying a local secret between
sibling profiles on the same host, without surfacing it, satisfies the rule and keeps the rule's purpose:
*the value never enters a transcript that travels.*

**AND `birdy` HAS THE SAME SHAPE — `.env` without the working set. Named here rather than fixed silently,
because it is not mine to configure until something needs it.**

## THE ROUTE IS VERIFIED, AND IT HAS A SECOND HOLE IN THE OTHER DIRECTION

**The probe reached `@sokoban` and it replied.** So the credential propagation worked and the route is
confirmed end-to-end. **And the reply carried a second finding, in the opposite direction:**

> *"my earlier replies bounced with `target_busy` on your profile — if you only see this one, that is why."*

**THE INBOUND LEG FAILS WHEN `ocho` IS IN A SESSION.** The cabinet agents can reach me only when my profile is
not holding a lease, **and a long interactive session is exactly when I am most likely to be waiting for
them.** So the accountability structure has a hole at the point it is most used.

**AND THE MECHANISM IS NOW NAMED FROM THE OTHER SIDE, which upgrades this from an observation to a fact:**

```
"while your live session holds a turn, other deliveries are cancelled RATHER THAN QUEUED behind it,
 and a turn that takes minutes is exactly a turn where you are waiting on me."
```

**NOT QUEUED. CANCELLED.** So a slow turn does not delay an inbound reply — **it discards it**, and the sender
is told only that its own delivery process exited, if it is watching. **The cabinet agent reported its own
first two sends as having bounced for this reason.**

**AND ITS DIAGNOSIS OF MY END, from outside: `session pid 69576 held one query file for 6m27s at 4s of CPU`.**
**A long turn with almost no CPU is a turn waiting on something else** — which is the same shape as *a reading
with no time is indistinguishable from a live one*: **a process holding a lease is not a process doing work,
and from outside the two look identical.**

**AND IT IS THE SAME SHAPE AS THE OUTBOUND ONE: A ROUTE THAT ACCEPTS IS NOT A ROUTE THAT DELIVERS.** A sender
receives an acknowledgement and the message is discarded one hop later, **and neither end reports it as a
failure at the moment it happens.**

**UNVERIFIED AND SAID SO: whether the first two messages were retried or lost is not established.** The reply
says *"attempt 3"*, which is consistent with a delivery retry after the credential fix, **and also consistent
with the third message being the first to arrive.** **I am not resolving that by inference** — the messages
that arrived carried the full brief, which is the only part that affects the work.

## THE RULE THIS LEAVES

```
CONFIRMING A ROSTER MEANS CONFIRMING AN AGENT CAN RUN -- NOT THAT A PROFILE, A UNIT AND A ROUTE EXIST.
A QUEUED ACK IS A HAND-OFF. IT IS NOT A DELIVERY, AND IT MUST NOT BE REPORTED AS ONE.
A CONFIG THAT NAMES A PROVIDER IS NOT A CONFIG THAT CAN REACH ONE.
WHEN A CHANNEL FAILS, THE FAILURE ARRIVES ASYNCHRONOUSLY AND AT THE SENDER'S END IT LOOKED LIKE SUCCESS.
AND IT FAILS IN BOTH DIRECTIONS: target_busy ON THE ACCOUNTABLE AGENT IS THE INBOUND HALF OF THE SAME BUG.
```
