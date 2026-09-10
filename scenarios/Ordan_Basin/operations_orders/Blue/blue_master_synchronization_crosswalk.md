# Blue Master Synchronization Crosswalk

> **Side-specific product:** For the Blue player and Blue staff. An optional controller may also use it, but controller participation is not required for baseline play. Do not provide it to the Red player during closed-plan play.

## 1. Purpose and Authority

This crosswalk provides one side-wide view of the Western Compact–Ordan Joint Land Corps plan. It links the corps tasks in B-00 to subordinate orders, operational phases, fires, passages, handoffs, reserve decisions, and player/controller checks. It summarizes rather than replaces the signed orders.

Use the following precedence when sources differ:

1. A later authenticated fragmentary order or in-play decision by the proper Blue headquarters, or a controller ruling under procedures agreed before play.
2. The applicable signed operations or support order.
3. This master crosswalk.
4. The operational graphics.

Report a conflict rather than silently choosing the most favorable interpretation. The [scenario specification](../../ordan_basin_scenario.md), [order of battle](../../game/order_of_battle.md), and [map source](../../map/ordan_basin_ao.map.json) govern shared runtime facts.

## 2. Shared Runtime Baseline

| Item | Baseline |
| --- | --- |
| Start | 12 September 2031, 0600 local time |
| Duration | 18 complete turns; 36 regular player phases; 9 days |
| Setup | Blue repositions first in columns `x=0–1`; Red repositions second; regular play begins with Blue |
| Cities | All seven begin neutral |
| Default disposition | Every Blue counter begins outside a city in the western setup zone |
| Unit information | Open; fog of war disabled |
| Crossings | Five: Dalen, Novar, Eren, North Pass, and Central Link |

PP South is the designated forward-passage lane through **Central Link Bridge**. The `OBJ C. LINK` label on the published Blue graphics refers to that same bridge. Phase lines, Guard Line Steel, the battle-handover line, and passage points are order and graphics control measures; they do not add scored cities or crossings to the engine map.

## 3. Order Hierarchy

| Order | Headquarters / formation | Parent | Primary contribution |
| --- | --- | --- | --- |
| [B-00](B-00_wco_joint_land_corps_opord.md) | Joint Land Corps | — | Campaign synchronization, main-effort shifts, reserve authority, crossing defense, and guard handover. |
| [B-10](B-10_1st_ordan_mechanized_division_opord.md) | 1st Ordan Mechanized Division | B-00 | Veyra, Novar, and Eren seizure/retention; southern defense; guard reception. |
| [B-1F](B-1F_1st_ordan_artillery_group_support_order.md) | 1st Ordan Artillery Group | B-10 | Fires for the capital, Novar/Eren, crossing retention, and southern guard reception. |
| [B-30](B-30_3rd_compact_armored_division_opord.md) | 3rd Compact Armored Division | B-00 | Crossing seizure, PP South control, forward passage, northern defense, and guard reception. |
| [B-3F](B-3F_3rd_division_artillery_group_support_order.md) | 3rd Division Artillery Group | B-30 | Fires for crossing seizure, passage, retention, and northern guard reception. |
| [B-60](B-60_6th_compact_mechanized_division_opord.md) | 6th Compact Mechanized Division | B-00 | Forward passage, sequential attacks on Kasar/Ruda/Selin, and Guard Line Steel. |
| [B-6F](B-6F_6th_division_artillery_group_support_order.md) | 6th Division Artillery Group | B-60 | Fires for passage, three eastern objectives, and guard disengagement. |

The 7th Coalition Armored Brigade has no separate base order. It remains directly under B-00 until the corps commander issues an authenticated committing order.

## 4. Corps Task-to-Order Crosswalk

| Task | Corps task and purpose | Lead order(s) | Supporting order(s) / control point |
| --- | --- | --- | --- |
| **B-C1** | Secure Veyra and western lines of communication to preserve the government and sustainment base. | B-10 | B-1F; B-30 protects the northern shoulder. |
| **B-C2** | Seize and retain the designated Arven crossings to deny Red access west of the river. | B-10 and B-30 | B-1F and B-3F; B-00 resolves seams and priorities. |
| **B-C3** | Pass the 6th Division at PP South and transfer the fight at the BHL without losing momentum. | B-30 and B-60 | B-3F and B-6F; both division headquarters confirm completion. |
| **B-C4** | Destroy Red forces sequentially at Kasar, Ruda, and Selin to disrupt the Eastern Army staging system. | B-60 | B-6F; corps reserve only by B-00 order. |
| **B-C5** | Establish Guard Line Steel and a defense in depth at the crossings to gain warning and preserve the defense. | B-60 for the guard; B-10/B-30 for reception | All three fire-support orders; B-00 controls transfer of the fight. |
| **B-C6** | Preserve combat power, infrastructure, and legitimacy to retain freedom of action. | All orders | 7th Brigade remains the corps mobile reserve unless committed. |

## 5. Phase Synchronization

Blue phases are **conditions-based**. The 18-turn limit is fixed, but no turn number by itself authorizes a phase change.

| Operational phase | Main effort | 1st Ordan Division | 3rd Compact Division | 6th Compact Division | Reserve / fires | Required transition condition |
| --- | --- | --- | --- | --- | --- | --- |
| **I — Seize crossings** | 3rd Division | Advance from the west to secure Veyra and seize Novar and Eren. | Seize assigned northern/central control measures and crossings; establish PP South. | Follow and support; preserve strength; prepare to pass. | 7th Brigade priority to 3rd; fires priority to crossing seizure. | Designated crossings controlled; PP South trafficable and secure; passage control established; 6th ready. |
| **II — Kasar** | 6th Division / 61st Brigade | Retain Veyra, Novar, and Eren. | Retain assigned crossings; control PP South; conduct passage and BHL handover. | Pass, accept the fight, and attack on Axis Black to defeat the Kasar force. | 7th Brigade and fires priority to 6th/61st. | Kasar force ineffective; routes open; 63rd provides temporary security; attack force postured for Ruda. |
| **III — Ruda** | 6th Division / 62nd Brigade | Retain southern sector and western routes. | Retain northern/central crossings and PP South. | Attack on Axis Blue; 61st fixes/protects; 63rd secures the rear near Kasar. | 7th remains uncommitted; fires priority to 6th/62nd. | Ruda force ineffective; rear secure; corridor security ready to transfer; force postured for Selin. |
| **IV — Selin** | 6th Division / 63rd Brigade | Retain Veyra, Novar, and Eren. | Retain assigned crossings and support the 6th Division rear. | Attack on Axis Brown; 62nd fixes/isolates; 61st secures Kasar–Ruda corridor. | Reserve prepared for Selin or guard transition; fires priority to 6th/63rd. | Selin force ineffective; guard can form; GL Steel/PL Bronze effective; receiving defense ready. |
| **V — Guard and defend** | 6th Division guard; corps defense at crossings | Establish southern defense and receive 62nd Brigade. | Establish northern defense and receive 63rd Brigade. | 63rd guards north of PL Bronze; 62nd south; 61st is division reserve; disengage on criteria. | 7th remains corps reserve; fires shift to contact/disengagement and handover. | Continues to scenario end or a subsequent authenticated operation. |

## 6. Passage, Handoff, and Retention Controls

| Event | Releasing / supporting formation | Receiving formation | Minimum confirmation |
| --- | --- | --- | --- |
| PP South opens at Central Link | 3rd Division | 6th Division | Bridge and approaches secure; movement control active; route and artillery displacement coordinated. |
| Fight transfers east of BHL | 3rd Division | 6th Division | Designated 6th rear element clear; positive liaison; both headquarters confirm time and location. |
| Kasar local security | 61st/6th lead | 63rd Brigade | Kasar force ineffective; routes trafficable; temporary security and reporting accepted. |
| Kasar–Ruda corridor security | 63rd / maneuver force | 61st Brigade | Ruda operation complete; rear routes understood; 61st able to protect the corridor. |
| Northern guard reception | 63rd Brigade / 6th Division | 3rd Division | Guard clear of BHL; contact, routes, fires, and responsibility positively transferred. |
| Southern guard reception | 62nd Brigade / 6th Division | 1st Division | Guard clear of BHL; contact, routes, fires, and responsibility positively transferred. |

No formation abandons an essential retention or security task until the receiving headquarters acknowledges it or B-00 explicitly accepts the gap.

## 7. Fires and Reserve Crosswalk

| Formation | Normal relationship | Priority progression | Key limitation |
| --- | --- | --- | --- |
| 1st Ordan Artillery Group | General support, 1st Division | Novar/Eren seizure; threatened crossing; southern guard reception | Cross-boundary support cannot uncover assigned essential tasks. |
| 3rd Division Artillery Group | General support, 3rd Division | Phase I crossing seizure; PP South passage; threatened crossing; northern guard reception | Maintain passage coverage until both divisions confirm completion. |
| 6th Division Artillery Group | General support, 6th Division | 61st at Kasar; 62nd at Ruda; 63rd at Selin; guard in contact/disengaging | Displace by echelon and preserve support to the current main effort. |
| 7th Coalition Armored Brigade | Corps reserve | 3rd Division in Phase I; 6th Division in Phases II–IV; threatened sector in Phase V | Reorientation is not commitment; combat employment requires authenticated corps direction. |

## 8. Principal Decision Points

| Decision | Authority | Minimum information | Result |
| --- | --- | --- | --- |
| **DP 1 — Begin Phase II** | Corps commander | Crossing control, PP South status, passage readiness, Red threat | Authorize passage and shift main effort to 6th Division. |
| **DP 2 — Commit corps reserve** | Corps commander | Threat/opportunity, supported formation status, routes, fires, sustainment, risk elsewhere | Issue task, purpose, command relationship, limit, and termination criteria. |
| **DP 3 — Begin Phase III** | Corps commander | Kasar force and route status; 6th Division strength; rear security; Ruda defense | Shift decisive operation and fires to 62nd Brigade. |
| **DP 4 — Begin Phase IV** | Corps commander | Ruda force status; corridor security; 61st readiness; Selin defense; support reach | Transfer rear security and shift decisive operation to 63rd Brigade. |
| **DP 5 — Begin Phase V** | Corps commander | Selin force status; 6th strength; GL Steel occupation; receiving-defense readiness | Form guard and crossing defense; place 61st in division reserve. |
| **DP 6 — Commit 6th Division reserve** | 6th Division commander | Guard penetration, disengagement freedom, artillery/route threat | Commit 61st within B-60 criteria. |
| **DP 7 — Disengage guard** | Corps commander; 6th commander within criteria | Delay achieved, Red main body, guard strength, route status, receiving force | Conduct controlled sector disengagement and shift fires. |
| **DP 8 — Transfer the fight** | Corps commander | Guard clear of BHL; positive contact/liaison; fires and route status | Transfer responsibility to 1st and 3rd Divisions; reconstitute 6th. |

## 9. Player/Controller Synchronization Checks

In controller-free baseline play, the Blue player or Blue team uses these checks to record decisions and maintain the order hierarchy. An optional controller may use the same list without changing the baseline authorities.

- Confirm all Blue starts are in `x=0–1`, outside urban hexes, before setup ends.
- Do not award city points during setup; all seven cities begin neutral.
- Track the five canonical crossings separately from graphics control measures.
- Record the condition and authorization for every operational-phase transition.
- Record task acceptance at PP South, the BHL, corridor-security transfers, and guard reception.
- Keep the 7th Brigade under corps control until an authenticated commitment is issued.
- Track artillery priority changes without changing parent command relationships.
- Record city-control duration, Blue and Red strength losses, reserve commitment, and final raw score for balance analysis.
