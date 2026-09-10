# Red Master Synchronization Crosswalk

> **Side-specific product:** For the Red player, Red staff, and scenario controller. Do not provide it to the Blue player during closed-plan play.

## 1. Purpose and Authority

This crosswalk provides one side-wide view of the Karsovian Eastern Army plan. It links R-00 to subordinate orders, projected turn windows, task purposes, fires, reserves, decision points, and controller checks. It summarizes rather than replaces the signed orders.

Use the following precedence when sources differ:

1. A later authenticated controller ruling or fragmentary order.
2. The applicable signed operations or support order.
3. This master crosswalk.
4. The operational graphics.

Report a conflict rather than silently choosing the most favorable interpretation. The [scenario specification](../../ordan_basin_scenario.md), [order of battle](../../game/order_of_battle.md), and [map source](../../map/ordan_basin_ao.map.json) govern shared runtime facts.

## 2. Shared Runtime Baseline

| Item | Baseline |
| --- | --- |
| Start | 12 September 2031, 0600 local time |
| Duration | 18 complete turns; 36 regular player phases; 9 days |
| Setup | Blue repositions first; Red repositions second in columns `x=10–11`; regular play begins with Blue |
| Cities | All seven begin neutral |
| Default disposition | Every Red counter begins outside a city in the eastern setup zone |
| Unit information | Open; fog of war disabled |
| Crossings | Five: Dalen, Novar, Eren, North Pass, and Central Link |

Projected turn windows organize the Red plan but do not guarantee that tactical conditions have been met. `PL Push`, `PL Punch`, `LOA Block`, boundaries, and other overlay symbols are player-enforced control measures rather than engine terrain.

## 3. Order Hierarchy

| Order | Headquarters / formation | Parent | Primary contribution |
| --- | --- | --- | --- |
| [R-00](R-00_karsovian_eastern_army_opord.md) | Karsovian Eastern Army | — | Army sequencing, main-effort shift, reserve authority, fires integration, and consolidation. |
| [R-10](R-10_4th_maneuver_corps_opord.md) | 4th Maneuver Corps | R-00 | Northern hook through Dalen, North Pass, and Central Link; later northern guard. |
| [R-11](R-11_8th_guards_armored_division_opord.md) | 8th Guards Armored Division | R-10 | Kasar, North Pass, and northern guard. |
| [R-12](R-12_15th_mechanized_division_opord.md) | 15th Mechanized Division | R-10 | Dalen, Central Link, and central-northern guard. |
| [R-1F](R-1F_4th_corps_artillery_group_support_order.md) | 4th Corps Artillery Group | R-10 | Northern fires and Phase III reinforcement of 9th Corps fires. |
| [R-20](R-20_9th_maneuver_corps_opord.md) | 9th Maneuver Corps | R-00 | Novar, Eren, Veyra, and central-southern consolidation. |
| [R-21](R-21_12th_armored_division_opord.md) | 12th Armored Division | R-20 | Selin, Eren, and southern guard. |
| [R-22](R-22_21st_mechanized_division_opord.md) | 21st Mechanized Division | R-20 | Novar, Veyra, and central guard. |
| [R-2F](R-2F_9th_corps_artillery_group_support_order.md) | 9th Corps Artillery Group | R-20 | Fires for Novar, Eren, Veyra, and retained objectives. |

The 5th Guards Armored Brigade has no separate base order. It begins under direct Eastern Army control, secures the Ruda route as an opening task, and resumes the Army-reserve role after local security is transferred.

## 4. Army Phase Synchronization

| Operational phase | Projected turns | Main effort | 4th Maneuver Corps | 9th Maneuver Corps | Army reserve / fires | Required transition condition |
| --- | ---: | --- | --- | --- | --- | --- |
| **I — Secure eastern basin and initial objectives** | 1–5 | 4th Corps / 15th Division | Seize Dalen; secure Kasar; fix North Pass. | Seize Novar; secure Selin; fix Eren. | 5th Brigade secures Ruda then transfers local security; fires priority to 4th/15th. | Dalen/Novar seized; Kasar/Ruda/Selin secure; North Pass/Eren fixed; corps postured. |
| **II — Seize remaining crossings** | 6–10 | 4th Corps | Seize Central Link and North Pass. | 12th Division seizes Eren; 21st isolates Veyra and establishes guards; Novar may lack a retain force. | 5th uncommitted near Novar; fires priority Central Link, North Pass, then Eren. | Principal crossings seized/trafficable; Veyra isolated; guards established; 9th ready to restore Novar and attack. |
| **III — Restore Novar and seize Veyra** | 11–15 | 9th Corps / 21st Division | Advance to PL Punch; establish northern/central guards; retain crossings; 4th Artillery reinforces 9th. | Restore and retain Novar; seize Veyra; retain Eren; protect both flanks. | 5th priority to 9th but remains uncommitted; fires restore Novar then mass on Veyra. | Veyra seized; resistance defeated; Novar/Eren secure; designated guards at PL Punch. |
| **IV — Consolidate, retain, and guard** | 16–18 | 9th Corps | Retain Dalen, North Pass, Central Link; guard northern LOA Block. | Retain Veyra, Novar, Eren; guard central/southern LOA Block. | 5th remains sole Army mobile reserve; fires support guards and threatened retained objectives. | Continue through scenario end with routes intact and a mobile response retained. |

## 5. Formation Task Crosswalk

| Formation | Phase I | Phase II | Phase III | Phase IV |
| --- | --- | --- | --- | --- |
| **8th Guards Armored Division** | Secure Kasar and fix North Pass. | Seize North Pass. | Advance to PL Punch; 82nd establishes northern guard; 81st retains North Pass. | Retain North Pass and guard northern LOA Block. |
| **15th Mechanized Division** | Seize Dalen. | Seize Central Link and block interference. | Retain Dalen/Link while establishing central-northern security. | Retain Dalen/Link and guard 4th Corps' central frontage. |
| **12th Armored Division** | Secure Selin and fix Eren. | Seize Eren. | Retain Eren; 121st establishes southern guard. | Retain Eren and guard southern LOA Block. |
| **21st Mechanized Division** | Seize Novar. | Isolate Veyra; establish PL Push and boundary guards; accept the temporary Novar gap. | Restore Novar, then seize Veyra; guard the flanks. | Retain Veyra/Novar and guard central LOA Block. |
| **5th Guards Armored Brigade** | Secure Ruda, transfer local security, and re-form as Army reserve. | Remain uncommitted near Novar. | Remain uncommitted with priority to 9th Corps. | Remain the sole mobile Army reserve. |

## 6. Fires, Routes, and Handoffs

| Event / relationship | Required synchronization |
| --- | --- |
| 4th Corps fires, Phases I–II | General support to 4th Corps; priority follows Dalen, Central Link, and North Pass tasks. |
| 9th Corps fires, Phases I–II | General support to 9th Corps; priority follows Novar, Selin/Eren, boundary guard, and Veyra isolation tasks. |
| Phase III reinforcing fires | 4th Artillery remains under 4th Corps control while reinforcing 9th Artillery; Army clears cross-boundary priorities and timing. |
| Ruda local-security transfer | 5th Brigade remains responsible until a receiving element accepts the route/security task and Army confirms reserve restoration. |
| Temporary Novar gap | 9th Corps reports the gap, route risk, 213th location, and restoration posture; the gap is deliberate but not self-correcting. |
| Veyra attack release | Restore and confirm the Novar route first unless the Army commander explicitly accepts simultaneous-action and isolation risk. |
| Guard disengagement | Guard reports contact, delay achieved, strength, and route; retain force acknowledges the handoff before responsibility transfers. |

## 7. Principal Decision Points

| Decision | Authority | Minimum information | Result |
| --- | --- | --- | --- |
| **DP 1 — Restore Army reserve** | Eastern Army commander | Ruda security transferred; routes open; 5th Brigade mission capable | Reposition 5th Brigade near Novar and restore reserve status. |
| **DP 2 — Begin Phase II** | Eastern Army commander | Dalen/Novar control; eastern hubs secure; North Pass/Eren fixed; corps readiness | Authorize coordinated attacks on North Pass, Central Link, and Eren. |
| **DP 3 — Commit Army reserve** | Eastern Army commander | Decisive threat/opportunity; supported-corps state; routes, fires, sustainment; risk elsewhere | Issue task, purpose, support, limit, and termination criteria. |
| **DP 4 — Shift main effort / begin Phase III** | Eastern Army commander | Crossings trafficable; 9th ready; 4th able to guard; fires and sustainment ready | Shift priority to 9th; restore Novar; initiate Veyra attack under stated risk criteria. |
| **DP 5 — Begin Phase IV** | Eastern Army commander | Veyra seized; resistance defeated; Novar/Eren secure; PL Punch guards established | Consolidate, retain objectives, form LOA Block guards, and restore reserve freedom. |
| **DP 6 — Disengage a guard** | Corps commander within Army criteria | Delay achieved; Blue main body identified; guard strength and route; retain-force readiness | Conduct controlled displacement and transfer responsibility. |

## 8. Controller Synchronization Checks

- Confirm all Red starts are in `x=10–11`, outside urban hexes, before setup ends.
- Do not award city points during setup; all seven cities begin neutral.
- Use the 18-turn horizon: Phase IV ends with Turn 18, not Turn 20.
- Record conditions and Army authorization for each main-effort or phase transition.
- Record the Ruda security transfer before treating the 5th Brigade as an uncommitted reserve.
- Track the Phase II Novar gap and the authority accepting any Veyra attack before the route is restored.
- Keep 4th Artillery under 4th Corps command during Phase III reinforcing fires.
- Require an authenticated order before committing the 5th Brigade to combat.
- Record city-control duration, Blue and Red strength losses, reserve commitment, and final raw score for balance analysis.
