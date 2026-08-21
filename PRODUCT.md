# Product

## Register

product

## Platform

web

## Users

Primary readers call InferHub Chat Completions (streaming) and need to know which alias is safe today for the shapes we actually probe. InferHub operators are secondary.

They arrive on GitHub Pages, already fluent in OpenAI request shapes.

## Product Purpose

InferHub Watch is a daily probe of InferHub `/v1/chat/completions` streaming shapes. Success is leaving knowing which alias passed today’s scoring checks.

## Positioning

A red cell means InferHub’s JSON missed the documented OpenAI shape for that check. It does not mean InferHub was down.

## Brand Personality

Blunt, forensic, calm. The voice names the wire field and the verdict. It does not hype models or narrate outages.

## Anti-references

This is not an OpenCrabs changelog or parser bug tracker.

## Design Principles

Latest results, past runs, then how we test — three containers, nothing else on the board.
Fail is a contract miss on the wire, never a status-page outage.
The alias is the request; the publisher sits under it, not in a second column.
Safe to use is the board headline: aliases that passed both scoring checks (tools + cache). Fail rows sit below.
Price is info; it never ranks and must not share pass/fail pill chrome.
How we test recedes. Verdicts and tables do not.
Prompt cache is scored on an ordinary streaming completion (no tools) with an ~8k-token prefix, not a short pad.
Write for InferHub API callers; OpenCrabs is not on the site.

## Accessibility & Inclusion

No numbered WCAG target. Tables must stay readable and focus must stay visible.
