# Whether the response includes a price

InferHub is a marketplace. Some publishers attach `usage.cost`, `market_cost`, `credit`; others return token counts only. This check never fails the suite.

## What we record

Whatever price-shaped fields appear on a non-stream tool call, or `tokens_only` if none do.

## Who should care

Anyone comparing InferHub invoices to token counters. Same alias can price differently when the resolved publisher changes.
