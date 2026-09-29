# Browser/engine model compatibility (S09)

The executable audit is
`browser_integration/test_engine_parity.py::test_combat_difference_audit_characterization`.
Run `uv run pytest tests/browser_integration -q` to check it and the shared
contracts. This report records the current baseline; differences below are not
requirements for future combat behavior.

## Shared live behavior

`fixtures/browser_contract.json` contains portable map/unit inputs and independent
expected geometry, movement costs, stacking limit (1), fire ranges and target
sets. Infinity travels as the string `impassable`. Both implementations must
match these expectations, rather than only matching each other. Negative odd
coordinate inputs expose the K21 mismatch recorded below. The fixture
reuses named maps to avoid repeated inputs; expected target lists are literal.
Geometry repeats the S02/S03 hand-tabulated vectors. Movement repeats S04's
corridors, terrain entry, blocked destinations, alternate routes and increased
stacking capacity. Fire cases include both column parities, exact/outside range,
friendly/ineffective/unplaced targets, artillery, and horizontal sqrt(3) distance.
Target sets are sorted; observation sequences retain their order.

## Combat differences

Ranges agree: infantry, armor and mechanized infantry 1; artillery 2.
The browser has no infantry firepower row. All four server entries in that row
are absent: infantry 1, mechanized infantry 1, armor 0.5, artillery 1.5.
Among the remaining 12 entries, six differ:

| Attacker | Target | Browser | Server |
| --- | --- | ---: | ---: |
| mechinf | infantry | 1 | 0.75 |
| mechinf | armor | 0.5 | 0.75 |
| armor | mechinf | 1 | 0.75 |
| armor | armor | 0.5 | 1 |
| armor | artillery | 1.5 | 1 |
| artillery | mechinf | 1 | 0.75 |

The six other entries agree. This is a passing characterization of the exact
current differences, not an assertion of whole-table parity. Authoritative
combat resolution remains on the server. The browser Combat object also lacks
server sight, detection probability, ineffective threshold, firepower scaling,
defensive firepower, and terrain multiplier tables; S09 does not require it to
resolve damage.

## Formats and lifecycle

- `Unit.fromPortable` preserves rich display fields. `fromPortable2` derives
  `uniqueId` as faction + space + longName and supplies regiment, name `1`,
  strength capacity 100, and null organization IDs. Both initialize action and
  ineffective flags to false; apply `partialObsUpdate` for current observations.
- Direct `Unit.Unit` construction registers the index but does not append to
  `Unit.units`. `remove()` clears placement/occupancy but keeps registry entries.
- Browser rich export dereferences the hex and throws for an unplaced unit;
  Python exports null. Fog is an observation value, not a valid loader hex ID.
  Observation updates remove fog-hidden/ineffective units from occupancy and
  restore them without duplication when visible again.
- Fire target helpers do not gate on `canMove` or `detected`. Browser fog is
  represented by an absent placement. The shared tests explicitly apply the
  observation after loading to avoid confusing loading with observation updates.
- Semantic map/unit fields are compared; raw serialized objects differ because
  browser units have display metadata and the Python map loader ignores paths.
  Browser path round trips are tested separately. Edge defects are not hidden by
  a raw round-trip comparison.
- S09 isolates SVG symbol creation with a recording boundary; actual SVG drawing
  and page workflows remain S10 onward. All model, geometry, occupancy, loading
  and targeting operations execute unchanged production ES modules over HTTP.

Confirmed browser replacement, edge/path identity and palette defects are
recorded in [KNOWN_ISSUES.md](KNOWN_ISSUES.md) as K01/K02/K10/K20. K21 records
negative odd columns: offsets (-1,0) and (-3,2) yield browser centers (-1,1)
and (-7,5), versus the Python/S03 expectations (-1,3) and (-7,7). These have
individual strict xfails; nonnegative generated grids and negative even columns
pass.
