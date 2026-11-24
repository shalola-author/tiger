# xTiger CK3 1.21 Agent Learnings
Keep this file concise (under ~100 lines). Merge/update existing bullets instead of appending duplicates.

## Codebase Map (Where Things Live)
- Buildings validator: `src/ck3/data/buildings.rs` — `Building::validate()` (top-level fields) + `fn validate_modifiers(vd, is_duchy_capital)` (all modifier collections, shared by fallback/override/trade_good_need). `_buildings.info` in the game documents the full structure.
- Trigger enum + tables: `src/ck3/tables/triggers.rs` (TRIGGER const). `trigger_comparevalue` in `src/trigger.rs` gates which triggers can be a bare value target.
- Modif name resolution: `lookup_modif` in `src/ck3/tables/modifs.rs` (templated `$X$_suffix` handlers). Game `modifiers.log` lists each tag with "Use areas:" (the ModifKinds).
- MAA modif lookup: `lookup_modif` in `src/ck3/tables/modifs.rs` — `stationed_$MEN_AT_ARMS_TYPE$_*` handlers check `Item::MenAtArmsBase` (base types such as `siege_weapon`, `light_cavalry`), NOT `Item::MenAtArms` (specific type keys).
- Confederation validator: `src/ck3/data/confederations.rs` — checks `confederation_base = house` for house-based confederations.
- Title types: `src/ck3/data/title_types.rs` — loads `common/title_types`, records prefixes with `landless = yes` (top-level or in `properties`). `TitleTypes::is_landless(key)` checks for `_<prefix>_` in a title key. Titles baronyless check moved to validate-time in `src/ck3/data/titles.rs` (`baronyless_counties` set + `validate()`) so landless-type counties (nf, merchant) are exempt from "county with no baronies!".

## Verified Patterns & Macros
- `validate_modifs` reports "unknown modifier `X`" via `ErrorKey::UnknownField`, so modifier errors count in the `unknown-field` bucket (not a separate `modifiers` bucket).
- Lowercase has no `starts_with`; use `name_lc.as_str().starts_with(..)` or `name_lc.strip_prefix_unchecked("x_").is_some()`. `strip_suffix_unchecked` returns `Option<Lowercase>`.
- Param modifier blocks accept BOTH `parameter` and `not_parameter` (claim each with `vd.field_item(name, Item::X)`); do NOT `req_field("parameter")` or not_parameter-only blocks error.
- Reuse `validate_modifiers(&mut vd, is_duchy_capital)` for any nested modifier collection; `ModifKinds::TradeMarket` for market_* (sell/buy price + trade_capacity modifiers are TradeMarket).
- `field_script_value_builder(name, sc_builder)` where `sc_builder: Fn(&Token)->ScopeContext`; `field_trigger_builder(name, Tooltipped::No, sc_builder)` for `{ trigger = {} }`.
- Duchy capital buildings identified by `flag = duchy_building` (not `type = duchy_capital`).
- House-based confederations identified by `confederation_base = house` (not just `house_based_confederation` bool).

## Reusable Scratch Scripts (CHECK BEFORE WRITING NEW SCRIPTS)
- `.scratch/check.ps1` — runs `cargo test`, builds release `ck3-tiger`, runs `--show-vanilla`, and refreshes summary (`powershell -ExecutionPolicy Bypass -File .\.scratch\check.ps1`).
- `.scratch/summarize_errors.py` — parses `.scratch/vanilla_1_21_gaps.txt` and updates `error_count.txt` + `gaps_summary.txt` (`python .scratch\summarize_errors.py`).
- `.scratch/prep_brief.py` — reads `LEARNINGS.md` + top 3 buckets from `gaps_summary.txt`, greps up to 8 sample lines per bucket from `vanilla_1_21_gaps.txt` (plus matching lines from `modifiers.log`/`triggers.log`/`effects.log` if present), writes `.scratch/BRIEF.md` (`python .scratch\prep_brief.py`).

## Dead Ends / Mistakes Not to Repeat
- The game `common/buildings/_buildings.info` doc misspells the field as `skip_internal_fullfilment`; real vanilla uses `skip_internal_fulfillment` — trust the `.txt` files, not the `.info` spelling.
- Trade good production modifiers (`trade_good_*_production_flat/add/mult`, `trade_category_*_production_mult`) are templated from `modifiers.log` — handle via prefix/suffix in `lookup_modif`, not MODIF_MAP.
- Triggers like `county_control_baseline`, `prosperity_level`, `governor_efficiency`, `house_power_score`, `trade_competitiveness`, `trade_income`, `trade_post_count`, `trade_post_limit`, `prosperity_rate`, `prosperity_rate_modifier`, `prosperity_towards_level_increase` are CompareValue triggers — must be `CompareValue` in TRIGGER table, not `UncheckedTodo`.
- `trade_good_category_level` is a Block trigger with `target` (TradeGoodCategory) and `value` (CompareValue), not a simple CompareValue.
- `stationed_<MAA base>_*` modifiers (e.g. `stationed_siege_weapon_damage_add`) reference MAA **base** types, so `lookup_modif` must check `Item::MenAtArmsBase`; checking `Item::MenAtArms` (specific type keys) causes false `missing-item` reports. The `$TAX_SLOT_TYPE$_add` catch-all must skip `stationed_*` prefixed modifiers (tax slot types are `clan_tax_slot`/`tax_slot`).

## 1.21 Fixes Applied (this session)
- Cycle 1: Trade good production modifiers (`trade_good_*_production_flat/add/mult`, `trade_category_*_production_mult`) via prefix/suffix handlers in `src/ck3/tables/modifs.rs` `lookup_modif`. Total errors 18,849 -> 16,497 -> 14,209.
- Cycle 2: Unknown token triggers (`county_control_baseline`, `prosperity_level`, `governor_efficiency`, `house_power_score`, `trade_competitiveness`, `trade_income`, `trade_post_count`, `trade_post_limit`, `prosperity_rate`, `prosperity_rate_modifier`, `prosperity_towards_level_increase`) changed from `UncheckedTodo` to `CompareValue` in `src/ck3/tables/triggers.rs`. Total errors 14,209 -> 12,945.
- Cycle 3: Duchy capital building detection fixed to check `flag = duchy_building` in `src/ck3/data/buildings.rs`. Total errors 12,945 -> 13,013 (validation 3,582 -> 3,359).
- Cycle 4: Confederation base detection fixed to check `confederation_base = house` in `src/ck3/data/confederations.rs`; `trade_good_category_level` fixed as Block trigger in `src/ck3/tables/triggers.rs`. Total errors 13,013 -> 12,992 (validation 3,359 -> 3,338).
- Cycle 5: "county with no baronies!" — noble/merchant family counties (`nf`, `merchant` prefixes) are landless by title type (`common/title_types/00_title_types.txt` sets `landless = yes`). Added `src/ck3/data/title_types.rs` loader; moved baronyless check to validate-time in `titles.rs`. Total errors 12,992 -> 10,003 (validation 3,338 -> 349).
- Cycle 6: #1 bucket `unknown-field` (2383 -> 1496) + `validation` (349 -> 61):
  - Added `add_trade_good_category_xp` effect with `TargetValue("target", TradeGoodCategory, "value")` in `effects.rs`
  - Fixed `province_size_level` trigger from `UncheckedTodo` to `CompareValue` in `triggers.rs`
  - Added `trade_good_category_level` as global function and LandedTitle promote in `datafunctions.rs` (tiger-tables)
  - Added `$TERRAIN_TYPE$_prosperity_growth`, `$TERRAIN_TYPE$_prosperity_growth_factor`, `$TERRAIN_TYPE$_district_*_cost`, `$TERRAIN_TYPE$_control`, `$TERRAIN_TYPE$_monthly_popular_opinion_change*`, `$TRADE_GOOD_CATEGORY$_xp_decline_mult`, `$MEN_AT_ARMS_TYPE$_reinforcement_rate` (using `MenAtArmsBase`) in `modifs.rs`
  - Added `name` field to `character_modifier`/`faith_character_modifier` blocks in `holysites.rs`
  Total errors 9649 -> 8302.
- Cycle 7: Top buckets `missing-item` + `unknown-field` via `ck3/tables/` subsystem:
  - Added DLC feature `silk_and_silver` to `DLC_FEATURES_CK3` in `misc.rs` (missing-item)
  - Handled special faith `BOOKMARK_CHARACTER_ANY_FAITH` in `bookmarks.rs` (missing-item)
  - Added 8 missing defines (NCharacter, NAdministrative, NCounty, NReligion, NRite, NScheme, NLaw, NTitle) in `defines.rs` (unknown-field)
  - Added missing modifier patterns in `modifs.rs`: terrain (`_province_size_baseline_add`, `_popular_opinion_add`, `_supply_limit_mult`), vassal stance (contributions, opinions, AI), government type (barter_goods/piety contributions), scheme type, district type, trade category (buy/sell price add, xp gain/decline add) (missing-item, unknown-field, modifiers)
- Cycle 8: #1 bucket `missing-item` (1795) via `src/ck3/tables/modifs.rs` `lookup_modif`:
  - `stationed_$MEN_AT_ARMS_TYPE$_*` handlers now check `Item::MenAtArmsBase` instead of `Item::MenAtArms`, so `stationed_<base>_*` modifiers (e.g. `stationed_siege_weapon_damage_add`) resolve against MAA base types.
  - The `$TAX_SLOT_TYPE$_add` catch-all now skips `stationed_*` prefixed modifiers so they reach the MAA base-type handlers instead of being misreported as missing tax slot types.
  - Verified in vanilla `common/men_at_arms_types/*.txt` (`type = siege_weapon` etc. are base types) and `common/modifier_definition_formats/00_unit_definitions.txt` (defines `stationed_<base>_*`); tax slot types are `clan_tax_slot`/`tax_slot`. No `allow_unknown`/`anything` added. cargo test passes with no regressions.