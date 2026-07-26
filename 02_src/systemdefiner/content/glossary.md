## Element hierarchy

Every flow and stock can be tracked in several nested elements:

- **material** — the total mass moved or stored (e.g. a printer, a bale of straw).
- **WC** (Water Content) and **DM** (Dry Matter) — material splits into these two. `material = WC + DM`.
- **TC** (Total Carbon) and **Ash_content** — dry matter splits into these two. `DM = TC + Ash_content`.
- **TOC** / **TIC** — total carbon splits into organic and inorganic carbon. `TC = TOC + TIC`.
- **CC** is an older name for TC used in some legacy studies — the two are never both present.

Each element is a fraction of its parent, so getting the fractions right at every level keeps the whole hierarchy mass-balanced.

## Process logic types

Every process (box in the flow diagram) can run one of these calculation modules, set on the Processes page:

- **FOMP** — First-Order Multiphasic (two-pool) Decay. Splits incoming carbon into a fast-decaying ("labile") and slow-decaying ("recalcitrant") pool, each decaying at its own rate. Used for compost, landfilled organics, soil carbon.
- **DSM** — Dynamic Stock Model. Tracks a stock of items (e.g. products in use) that leave the stock over time according to a lifetime distribution, rather than decaying continuously.
- **LFG** — Landfill Gas model (UNFCCC AM-Tool-04 methodology). Models methane and CO2 generation from landfilled waste using a multi-pool first-order decay, with capture/oxidation factors.
- **FlowCap** — Capacity-limited routing. Caps an outgoing flow at a maximum throughput; anything above the cap is routed to a separate "overflow" flow instead.
- **Input_Substitution** — Models secondary/recycled material displacing a fixed virgin-material demand, with any shortfall or surplus tracked explicitly.
- **BOM_Assembler** — Bill-of-Materials Assembler. Builds an outgoing flow's composition from a fixed recipe of input materials (e.g. assembling a product from its components), rather than from transfer coefficients.

Processes that don't need any of these just use plain transfer coefficients (TCs) to split their outflows.

## Monte Carlo Operation

When a Monte Carlo parameter is enabled, its sampled value is applied to the target (a TC, a flow, a DSM/FOMP parameter, etc.) using one of three operations:

- **set** — replace the target's value with the sampled value outright.
- **multiply** — multiply the target's existing value by the sampled value (use for a relative/percentage uncertainty).
- **add** — add the sampled value to the target's existing value (use for an absolute uncertainty).

## Scenarios

A scenario is a named set of overrides — e.g. a different TC, a different flow value — applied on top of the baseline model for an alternative what-if run. Up to four scenarios can be selected to run together in Model Configuration; each one is calculated as its own independent variant of the baseline system, so results can be compared side by side.
