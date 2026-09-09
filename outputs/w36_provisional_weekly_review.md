# Provisional weekly review — W36 snapshot, 2026-09-09

**Status: not approval-ready.** This is a review aid, not a decision-log update and not an instruction to change Meta campaigns.

## Readiness record

- The Meta lead dry-run found 9 leads across 4 forms; all were already current. No Lead records were created or changed.
- The weekly-performance dry-run found 5 W35 refreshes and 5 inserts (including the W36 rows); all Meta ads mapped to existing Grist Ads records. No ad was created.
- `Weekly_runs` was then refreshed/inserted as reviewed, and derived metrics, the full export, attachments, and all three upload bundles were rebuilt.
- `weekly_upload_data.zip`, `weekly_upload_assets.zip`, and `weekly_upload_context.zip` all pass ZIP integrity checks. Every required bundled file was present and readable. The fresh bundle manifest is timestamped `2026-09-09T06:43:56Z`.

## Approval gates

1. **W36 is still in progress.** It ends on 2026-09-09, while the snapshot was taken at 06:43 UTC / morning local time. The last part of the day and any Meta reporting finalization are absent. Consequently it is not the latest completed data week required for a final W37 decision.
2. **Intent is now reconciled.** After the initial export, all four W36 rows were corrected to `Intended_run = true`. This matches the W36 decision log: Men = `Mens Ad B`, `M 2609_1`; Women = `Womens Ad G`, `W 2609_1`. Confirm that status again in the final post-close refresh.
3. The lead sync detected seven pre-existing duplicate phone/email keys. It changed none. This does not block the weekly CPL calculation, but it should be handled as a separate CRM-data-quality task.

## Snapshot performance (not final)

| Campaign | Ad | Spend (ILS) | Leads | CPL (ILS) | Current contiguous run | Rule result if W36 closes unchanged |
|---|---|---:|---:|---:|---|---|
| Men | M 2609_1 | 73.08 | 2 | 36.54 | 76.07 / 2 / 38.04 (W35–W36) | Keep: rule 1 |
| Men | Mens Ad B | 100.25 | 0 | — | 378.55 / 10 / 37.86 (W33–W36) | Replace: rule 5 |
| Women | Womens Ad G | 105.98 | 6 | 17.66 | 198.72 / 8 / 24.84 (W35–W36) | Keep: rule 1 |
| Women | W 2609_1 | 63.87 | 0 | — | 63.87 / 0 / — (W36) | Replace: rule 5 |

The snapshot portfolio spent 343.18 ILS for 8 leads (blended CPL 42.90). This is descriptive only; it must not be compared as a completed week until the approval gates close.

### What is notable

- `M 2609_1` has a strong first partial read: 2 leads at 36.54 ILS CPL. Its evidence is still low-sample (2 weekly and 2 lifetime leads).
- `Mens Ad B` moved from 4 W35 leads at 26.14 CPL to 0 leads after 100.25 ILS. Because its run has already spent 378.55 ILS, the rule is decisive if the completed-week result remains this way.
- `Womens Ad G` improved from 2 W35 leads at 46.37 CPL to 6 at 17.66 CPL. This is the strongest signal in the snapshot, but the current day is incomplete and it is only a two-week run.
- `W 2609_1` has had no lead after 63.87 ILS. It has just crossed the current-run protection limit, so the final few hours of W36 materially matter.

## Conditional W37 portfolio — only if the gates close without material change

| Campaign | Keep | Replacement | Why this is the rule-led pick |
|---|---|---|---|
| Men | `M 2609_1` | Reuse `Mens Ad J` | One replacement slot; a complete-new men's ad launched in W36, so select the top strong inactive reuse candidate. `Mens Ad J` has the lowest recent prior-run CPL among strong male candidates: 41.23 (W33–W35), and 39.49 lifetime CPL over 97 leads. |
| Women | `Womens Ad G` | New ad using the `W 2603_1` creative and a new primary text | `W 2603_1` is the top strong inactive reuse candidate: 26.70 recent-run CPL (W23–W35) and 35.82 lifetime CPL over 17 leads. The proposed version retains its proven creative/headline and replaces the text with the new `Shake the routine` text below. |

The men's proposal is a direct conditional application of the written rule. The women's proposal is a human-proposed creative adaptation: it is neither an unchanged full-ad reuse nor a complete-new ad. Under the current weekly prompt it is therefore a reshuffle-type exception, which normally appears only as a fallback for a complete-new recommendation. This preview records the option without changing that policy or treating it as automatically approved.

### Proposed W 2603_1 text variant — new ad, name to be assigned

**Headline carried by the creative:** `לנער את השגרה`

בא לך ערב אחד בשבוע שהוא רק שלך — לא עוד משימה, ולא עוד אימון?  
באייקידו זזים, לומדים משהו חדש, ויוצאים קצת מהמסלול הרגיל.

🥋 להניע את הגוף, להתחזק ולשפר שיווי משקל  
🥋 ללמוד מיומנות שמתגלה בה עוד משהו משיעור לשיעור  
🥋 להתאמן עם אנשים באווירה נעימה, בלי תחרות ובלי צורך להוכיח דבר

האימונים במרכז באר שבע מתאימים גם למי שמתחילה מאפס.  
לחצי לפרטים ובואי לשיעור ניסיון ללא התחייבות.

Proposed existing tags: Hook = `Care Load / No Time`; Promise = `Body Capability`; Structure = `Checklist`. No new tag is required.

### Reuse ranking evidence

| Campaign | Candidate | Strength | Most recent prior-run CPL | Lifetime CPL | Notes |
|---|---|---|---:|---:|---|
| Men | Mens Ad J | Strong | 41.23 | 39.49 | Rule-selected; most recent run ended W35 after a zero-lead week. |
| Men | M 2607_1 | Strong | 43.51 | 43.51 | Next eligible male candidate; 12 leads, but its W31–W33 run ended poorly. |
| Men | M 2605_1 | Strong | 51.78 | 51.78 | Third; four leads only. |
| Women | W 2603_1 | Strong | 26.70 | 35.82 | Rule-selected; high efficiency but known low-delivery risk. |
| Women | W 2605_1 | Strong | 51.78 | 51.78 | Shares `Quiet Space - Bullet Calm` text with W 2603_1; not relevant unless two slots open. |
| Women | Womens Ad O | Strong | 58.50 | 58.50 | Third-ranked strong candidate. |
| Women | Womens Ad A | Strong | 62.02 | 44.12 | Strong by lifetime CPL only; not ahead of W 2603_1 on the prescribed sort. |

## Component, image, and constraint review

The actual creative files were inspected, using the canonical attachment filenames from the manifest.

| Proposed W37 ad | Canonical creative file | Image–copy assessment | Existing tags |
|---|---|---|---|
| M 2609_1 (keep) | `Creatives/M 2609_1.png` | Male pair, wrist control, and an off-balance posture directly support “control in the moment, not by force” and the copy’s timing/coordination claim. | Line Art; Instructional/Demonstration; Direct; Strength Without Force; Non-violent Power; Short lines |
| Mens Ad J (reuse) | `Creatives/Mens Ad J.png` | A two-person throw gives the “quiet power / control” claim a clear technique-based visual. The copy is more reflective than the project’s preferred sponsored tone, so review its wording before relaunch. | Line Art; Dynamic/Throw; Reflective; Calm Under Pressure; Strength Without Force; Question Hook |
| Womens Ad G (keep) | `Creatives/Womens Ad G.png` | A woman training with a male partner reads as active, welcoming dojo practice. It supports confidence and body capability; its “screens/energy” hook is carried principally by copy rather than image. | Illustration–Poster; Instructional/Demonstration; Poetic; Confidence/Self-Trust; Energy/Fatigue/Screens |
| New W 2603_1 creative/text variant | `Creatives/W 2603_1.png` | The woman viewed from behind can support audience self-projection; the prominent, engaged male partner and the active technique give `לנער את השגרה` a concrete routine-breaking energy. The new text follows that promise with a personal-evening, movement, learning, and welcoming-practice frame. | Illustration–Photo Art; Instructional/Demonstration; Playful; Energy/Renewal; new text: Care Load/No Time; Body Capability; Checklist |

No media, headline, or primary text would be duplicated within the provisional W37 men’s or women’s campaign: `Womens Ad G` uses `Screens To Energy`, not the proposed new text. The image/headline text combination has been reviewed; the media tag `Illustration - Photo Art` remains an inaccurate description of the actual photograph and should not be used as a visual conclusion.

## Draft decision-log entry — do not add yet

```markdown
# Plan for 2026-W37 (assessing 2026-W36)

### Weeks

- **Assessed (data) week:** 2026-W36
- **Decision / planned week:** 2026-W37

### Ads active in assessed week (2026-W36)

- Men: M 2609_1, Mens Ad B
- Women: Womens Ad G, W 2609_1

### Ads planned for decision week (2026-W37)

- Men: M 2609_1, Mens Ad J [conditional]
- Women: Womens Ad G, new ad using the W 2603_1 creative and the proposed text variant [conditional; policy exception requires approval]

---

End of Plan 2026-W37

---
```

Do not approve or insert this draft until the W36 refresh has run after close and the final rule outcomes are checked again. The proposed women’s text variant also requires explicit approval as a reshuffle-type exception under the current policy.

## Finalization sequence

1. Refresh Meta data after W36 has closed and reporting has settled.
2. Confirm that the four intended W36 ads remain correctly flagged in the refreshed data.
3. Rebuild exports and repeat the compact rule/candidate check.
4. Present the final decision-log entry and recommendations for your explicit approval; make no Meta campaign or decision-log change unless separately authorized.
