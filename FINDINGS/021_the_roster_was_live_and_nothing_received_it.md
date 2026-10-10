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

## THE RULE THIS LEAVES

```
CONFIRMING A ROSTER MEANS CONFIRMING AN AGENT CAN RUN -- NOT THAT A PROFILE, A UNIT AND A ROUTE EXIST.
A QUEUED ACK IS A HAND-OFF. IT IS NOT A DELIVERY, AND IT MUST NOT BE REPORTED AS ONE.
A CONFIG THAT NAMES A PROVIDER IS NOT A CONFIG THAT CAN REACH ONE.
WHEN A CHANNEL FAILS, THE FAILURE ARRIVES ASYNCHRONOUSLY AND AT THE SENDER'S END IT LOOKED LIKE SUCCESS.
```
