# Whether the response includes a price

InferHub bills consumers in USDC. This check never fails. It copies whatever price-shaped fields appear on the **streaming** usage payload.

## What we record

`cost`, `market_cost`, `gateway_cost`, and/or `credit` when present, otherwise `tokens_only`. Those fields are **not** treated as one unit: some routes send `credit`, others send `cost*`. We do not convert them.

## Who should care

Anyone comparing an InferHub invoice to `usage` on the wire. The same alias can price differently when the resolved publisher changes.
