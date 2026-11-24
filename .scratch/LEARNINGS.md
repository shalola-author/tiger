# xTiger CK3 1.21 Agent Learnings
Keep this file concise (under ~100 lines). Merge/update existing bullets instead of appending duplicates.

## Codebase Map (Where Things Live)
- Buildings validator: `src/ck3/data/buildings.rs` — `Building::validate()` (top-level fields) + `fn validate_modifiers(vd, is_duchy_capital)` (all modifier collections, shared by fallback/override/trade_good_need). `_buildings.info` in the game documents the full structure.
- Trigger enum + tables: `src/ck3/tables/triggers.rs` (TRIGGER const). `trigger_comparevalue` in `src/trigger.rs` gates which triggers can be a bare value target.
- Modif name resolution: `lookup_modif` in `src/ck3/tables/modifs.rs` (templated `$X$_suffix` handlers). Game `modifiers.log` lists each tag with "Use areas:" (the ModifKinds).
- MAA modif lookup: `lookup_modif` in `src/ck3/tables/modifs.rs` — `stationed_$MEN_AT_ARMS_TYPE$_*` handlers check `Item::MenAtArmsBase` (base types such as `siege_weapon`, `light_cavalry`), NOT `Item::MenAtArms` (specific type keys).
- Confederation validator: `src/ck3/data/confederations.rs` — checks `confederation_base = house` for house-based confederations.
- Defines whitelist: `src/ck3/tables/defines.rs` (`DEFINES` const + `DEFINES_MAP`); missing defines produce `error(unknown-field): unknown define N*|X`.
- Title types: `src/ck3/data/title_types.rs` — loads `common/title_types`, records prefixes with `landless = yes` (top-level or in `properties`). `TitleTypes::is_landless(key)` checks for `_<prefix>_` in a title key. Titles baronyless check moved to validate-time in `src/ck3/data/titles.rs` (`baronyless_counties` set + `validate()`) so landless-type counties (nf, merchant) are exempt from "county with no baronies!".
- Province history validator: `src/ck3/data/prov_history.rs` — `validate_common` recognizes province-history fields (culture, religion, buildings, special_building_slot/district, districts, effect); any other field produces `error(unknown-field): unknown field X`.

## Verified Patterns & Macros
- `validate_modifs` reports "unknown modifier `X`" via `ErrorKey::UnknownField`, so modifier errors count in the `unknown-field` bucket (not a separate `modifiers` bucket).
- Lowercase has no `starts_with`; use `name_lc.as_str().starts_with(..)` or `name_lc.strip_prefix_unchecked("x_").is_some()`. `strip_suffix_unchecked` returns `Option<Lowercase>`.
- Param modifier blocks accept BOTH `parameter` and `not_parameter` (claim each with `vd.field_item(name, Item::X)`); do NOT `req_field("parameter")` or not_parameter-only blocks error. Applies to buildings `province_government_modifier`/`character_government_modifier` too (vanilla uses `not_parameter = government_is_tribal` 936x).
- `modif_check(name, &s, Item::X, kinds, ...)` returns `Some(kinds)` EVEN when the item lookup fails (it only reports). Pick `kinds` to match the weakest vanilla context at the call site.
- `maa` is a hardcoded wildcard for "all men-at-arms types" (`stationed_maa_*` in `common/modifier_definition_formats/00_unit_definitions.txt`), NOT an item in `Item::MenAtArmsBase` — special-case it in stationed handlers.
- Handler ORDER inside `lookup_modif` is load-bearing: specific prefix handlers (`trade_category_`, `trade_good_`, `stationed_`) must run BEFORE generic suffix catch-alls (`$TAX_SLOT_TYPE$_add`), and a new suffix handler must be checked against names that later prefix handlers own.
- Reuse `validate_modifiers(&mut vd, is_duchy_capital)` for any nested modifier collection; `ModifKinds::TradeMarket` for market_* (sell/buy price + trade_capacity modifiers are TradeMarket).
- `field_script_value_builder(name, sc_builder)` where `sc_builder: Fn(&Token)->ScopeContext`; `field_trigger_builder(name, Tooltipped::No, sc_builder)` for `{ trigger = {} }`.
- `trigger_comparevalue(name, data)` derives CompareValue from the TRIGGER table type — changing `UncheckedTodo`→`CompareValue` in `src/ck3/tables/triggers.rs` is the complete fix for triggers used as bare value targets (`value = scope.trigger`); no separate list to update.
- Duchy capital buildings identified by `flag = duchy_building` (not `type = duchy_capital`).
- House-based confederations identified by `confederation_base = house` (not just `house_based_confederation` bool).
- Templated MAA modifiers (both `stationed_<base>_*` and `<base>_*` patterns) are not all defined in `common/modifier_definition_formats/` — skip `ModifierFormat` validation for them via `is_templated_maa_modifier()` in `src/modif.rs` to avoid false `missing-item` errors.
- Building effects (`remove_building`, `downgrade_building_effect`) accept scope references (`scope:selected_item`, `scope:destroyed_building_type`) — use `ScopeOrItem(Scopes::Building, Item::Building)` in `src/ck3/tables/effects.rs` instead of `Item(Item::Building)`.

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
- Do NOT give one tag family a single ModifKinds when its suffixes differ: per `modifiers.log`, `$TRADE_GOOD_CATEGORY$_xp_gain_add/mult` = character+trade_route, `_xp_decline_add/mult` = character, while buy/sell price = char/prov/county/route/market and `_production_mult` = char/prov/county.
- `stationed_*` modifiers are valid inside COUNTY blocks (vanilla `duchy_capital_county_modifier` in `00_duchy_capital_buildings.txt`) — their kinds must be `Province | County`, not Province-only, or you get 900+ "is a modifier for province but expected county".
- Generic suffix handlers placed early in `lookup_modif` shadow later prefix handlers: `_xp_gain_mult` (lifestyle/trait) swallowed `trade_category_*_xp_gain_mult` (782 false errors), and the early MAA handler returned Province-only for `stationed_*`. Both fixed in cycle 9 — keep prefix handlers first.
- `history` bucket (1106) is vanilla data errors ("title has no holder at X", "holder not alive at X") — not fixable via validator code; do not chase.
- `unknown-field` (#1, 1367) is multi-subsystem: defines (defines.rs), unknown-token triggers (triggers.rs CompareValue), and scattered `unknown field X` validators — no single subsystem fixes all of it.
- Vanilla building effects (`remove_building`, `downgrade_building_effect`) use scope references (`scope:selected_item`, `scope:destroyed_building_type`) — do not use `Item(Item::Building)` which rejects valid scope refs; use `ScopeOrItem` instead.
- Not all templated MAA modifiers are defined in `common/modifier_definition_formats/` (e.g. `elephant_cavalry_control_value_add`, `stationed_elephant_cavalry_control_value_add`) — skip `ModifierFormat` validation for these patterns to avoid false `missing-item` errors.

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
- Cycle 9: #1 `missing-item` (1795 -> 497) + #2 `field-missing` (1522 -> 39) + `modifiers` (1069 -> 69) via `src/ck3/tables/modifs.rs` + `src/ck3/data/buildings.rs`:
  - `lookup_modif`: `trade_category_*_xp_gain_*` no longer swallowed by the lifestyle/trait `_xp_gain_mult`/`_xp_gain_add` handlers (also fixed the literal `{s}` message); trade category xp use areas split per `modifiers.log` (xp_gain = char+trade_route, xp_decline = char); trade category buy/sell/xp group moved above the `$TAX_SLOT_TYPE$_add` catch-all.
  - `stationed_*` handlers unified: early MAA handler no longer intercepts `stationed_` (was Province-only); dedicated stationed handler returns `Province | County`; `stationed_maa_*` wildcard special-cased.
  - `buildings.rs`: `province/character_government_modifier` accept `parameter`+`not_parameter` (no `req_field`); `county_potential_trade_good_modifier` kinds `County | Province` (vanilla uses `trade_good_*_production_add` inside).
  - Verified in `modifiers.log`, `00_unit_definitions.txt`, `00_duchy_capital_buildings.txt`, `00_villages_district_buildings.txt`, `01_duchy_office_buildings.txt`, culture traditions. cargo test: 37 passed. Total errors 7922 -> 4141. Remaining missing-item is title/character history (history subsystem).
- Cycle 10: #1 bucket `unknown-field` via `src/ck3/tables/triggers.rs` + `src/ck3/tables/defines.rs` (+ pre-existing structure fixes in doctrines.rs/religions.rs):
  - triggers.rs: 10 value-returning triggers `UncheckedTodo`→`CompareValue` (acumen, base_popular_opinion, current_capacity, district_slots, num_districts, num_trade_markets, num_trade_routes, popular_opinion, province_size, total_monthly_tax_income) so they are accepted as bare value targets; addresses the unknown-token slice of unknown-field.
  - defines.rs: registered 23 missing 1.21 defines (NCulture, NDomain, NDynasty, NGUI, NGraphics, NMercenary, NProvince, NTravel) for the unknown-define slice of unknown-field; all verified present in vanilla common/defines/00_defines.txt + category files.
  - doctrines.rs: validate historical_glossary block on Doctrine/Tenet (vanilla common/religion/doctrine_types/20_doctrines.txt, tenet_types/00_tenet_types.txt).
  - religions.rs: accept optional `history` bool on Rite (vanilla common/religion/rite_types/00_rite_types.txt, history = yes).
  - No allow_unknown/anything/wildcard skips added. cargo test: 37 passed.
- Cycle 11: #1 bucket `unknown-field` (1367 -> 1246) via `src/ck3/tables/defines.rs`:
  - Added missing NDomicile defines: BACKGROUND_LAYER_DEPTH, FOREGROUND_LAYER_DEPTH, BUILDING_LAYER_DEPTH_DEFAULT, MERCHANT_ACUMEN_LEVEL_2/3/4_THRESHOLD (6 keys)
  - Added missing NConfederation define: CONFEDERATION_ASPIRATION_COOLDOWN_DAYS (1 key)
  - Added entire NTrade category (37 keys): BASE_COMPETITIVENESS, BASE_MAX_TRADE_ROUTE_LENGTH, BASE_MAX_TRADE_ROUTES, BASE_MAX_COMMISSION_ROUTES, MAX_DISTRIBUTION_ROUTES_PER_TIER, BASE_MAX_TRADE_MARKETS_ON_ROUTE, MAX_TRADE_MARKETS_ON_DISTRIBUTION_ROUTE, BASE_MAX_TRADE_GOODS_ON_ROUTE, MAX_TRADE_GOODS_ON_ROUTE_CAP, BASE_TRADE_CAPACITY, TRADER_APTITUDE_LEVEL_BREAKPOINTS, DEFAULT_TRADE_TASK_ANIMATION, BUY/SELL_PRICE_SCALAR, BUY/SELL_PRICE_PROSPERITY_*, MAX_RECOMMENDED_GOODS, RECOMMENDED_GOODS_TO_SHOW_ON_MAP, TOP_GOODS_BY_SURPLUS_COUNT, GOODS_TO_SHOW_ON_MAP_ICON, NEEDS_TO_SHOW_IN_HOLDING_TOOLTIP, BASE_TRADE_POST_LIMIT, TRADE_CATEGORY_BASE_MONTHLY_XP_GAIN/DECLINE, TRADE_CATEGORY_XP_LEVEL_THRESHOLD, TRADE_ROUTE_VALUE_CHANGE_NOTIFICATION_THRESHOLD, TRADE_ROUTE_INCOME_CAUSE_MIN_SHARE_OF_CHANGE, CHANGE_TOLL_LEVEL_COOLDOWN, DEFAULT_TOLL_EXCEPTION_DURATION, DEFAULT_TOLL_LEVEL, MIN_DISTRIBUTION_ROUTE_TIER, MAX_COMMISSION_IDLE_TIME, MIN_MERCHANT_MARRIAGE_CANDIDATES
  - All verified in vanilla common/defines/00_defines.txt. No allow_unknown/anything added. cargo test: 37 passed. Total errors 4053 -> 3932.
- Cycle 12: #1 bucket `unknown-field` (1246 -> 1037) via `src/ck3/data/prov_history.rs`:
  - Recognized `special_district_slot` (a value, like `special_building_slot`) and `trade_post` (a block) in `validate_common`, eliminating 209 unknown-field errors in `history/provinces/*.txt`. Verified in vanilla `history/provinces/k_azuma.txt` / `k_italy.txt`. No allow_unknown/anything added. cargo test: 37 passed. Total errors 3932 -> 3723. `history` is now the top bucket (1106, vanilla data errors — not fixable via validator code).- Cycle 14 (Round 5): #1 fixable bucket `unknown-field` (1011 -> 945) + total (3688 -> 3622) via `src/ck3/tables/defines.rs`:
  - Added 66 missing 1.21 defines across 11 categories: NGameAudioEffects (8), NGameIcons (2), NGraphics (6 new), NMapColors (2), NMapIcon (5), NMapModes (24), NHoldingSprawl (14 new), NJominiPortraits (1 new), NTextColoring (2 new), NTextLinkAudio (1 new), NTravel (1)
  - All verified in vanilla common/defines/audio/00_audio.txt, graphic/00_graphics.txt, jomini/portraits.txt, jomini/text_coloring.txt. No allow_unknown/anything added. cargo test: 37 passed.
- Cycle 13: #1 bucket unknown-field (1037 -> 1011) + missing-item (497 -> 488) via src/ck3/tables/defines.rs + src/modif.rs + src/ck3/tables/effects.rs:
  - Added missing NAI defines (AI_ADDITIONAL_MONTHS_OF_GROSS_INCOME, AI_APPLY_POTENTIAL_MERCS_TO_MILITARY_STRENGTH_CURRENCY_THRESHOLD, AI_BOLDNESS_ADJUSTMENT_FACTOR_POTENTIAL_MERC_POWER), NTrade defines (NEEDS_TO_SHOW_IN_HOLDING_TOOLTIP + 9 AI trade defines), NTradeRouteGraphics defines (6 keys) to defines.rs
  - Added is_templated_maa_modifier() helper in modif.rs to skip ModifierFormat validation for templated MAA modifiers (both stationed and non-stationed _damage_add/mult, _pursuit_add/mult, _screen_add/mult, _siege_value_add/mult, _toughness_add/mult, _control_value_add/mult, _maintenance_mult, _maintenance_low_modifier, _maintenance_high_modifier, _max_size_add/mult, _recruitment_cost_mult, _reinforcement_rate)
  - Changed remove_building and downgrade_building_effect from Item(Item::Building) to ScopeOrItem(Scopes::Building, Item::Building) in effects.rs to accept scope references (scope:selected_item, scope:destroyed_building_type)
  - Verified in vanilla common/defines/00_defines.txt, common/defines/ai/00_ai.txt, common/defines/graphic/00_graphics.txt, common/buildings/regular_district_buildings/00_household_district_buildings.txt, common/scripted_effects/00_building_effects.txt. No allow_unknown/anything added. cargo test: 37 passed. Total errors 3711 -> 3688.
- Cycle 14 (Round 5): #1 fixable bucket `unknown-field` (1011 -> 945) + total (3688 -> 3622) via `src/ck3/tables/defines.rs`:
  - Added 66 missing 1.21 defines across 11 categories: NGameAudioEffects (8), NGameIcons (2), NGraphics (6 new), NMapColors (2), NMapIcon (5), NMapModes (24), NHoldingSprawl (14 new), NJominiPortraits (1 new), NTextColoring (2 new), NTextLinkAudio (1 new), NTravel (1)
  - All verified in vanilla common/defines/audio/00_audio.txt, graphic/00_graphics.txt, jomini/portraits.txt, jomini/text_coloring.txt. No allow_unknown/anything added. cargo test: 37 passed.
- Round 6: #1 fixable `unknown-field` (945 -> 935) + total (3622 -> 3612) via `src/ck3/tables/defines.rs` + `src/ck3/tables/triggers.rs`:
  - Added 3 missing defines: NMapModes|POPULAR_OPINION_COLORS (Color), NGui|MAX_INLINE_BUILDING_TRACK_LENGTH (Number), NGui|MAX_MODIFIER_STACKS_IN_TOOLTIP (Number); verified in vanilla common/defines/graphic/00_graphics.txt.
  - Changed 5 triggers from UncheckedTodo to CompareValue: max_capacity (TradeRoute), max_commission_routes (Character), num_commission_routes (Character), max_trade_routes (Character), max_trade_markets (TradeRoute).
  - No allow_unknown/anything added. cargo test: 37 passed.
