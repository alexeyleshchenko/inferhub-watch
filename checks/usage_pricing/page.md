# Whether the response includes a price

InferHub bills consumers in USDC. This check never fails. It copies whatever price-shaped fields appear on the **streaming** usage payload.

## What we record

`cost`, `market_cost`, `gateway_cost`, and/or `credit` when present. Those fields are not treated as one unit; we do not convert them. The same alias can price differently when the resolved publisher changes. A cell with no price field is still info, never a fail.
