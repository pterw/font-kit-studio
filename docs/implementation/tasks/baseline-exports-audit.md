# Baseline import/export audit

Read-only application audit of `C:/Users/peter/Downloads/font_kit_studio_v0.1.1.html`, against the supplied responsive rows design. No application, tests, or Git state changed. Graph transport was unavailable in the parent's Verify-tier attempts; generation and coverage remain unknown. Direct source and fresh isolated Chromium page reproductions supply the evidence below.

## Confirmed defects

1. **Malformed nested rows retain hidden session assets in JSON exports.** `hydrateSlot` converts a nested row to text, but spreads all original fields onto that leaf (1768–1786). Its `children` field survives. `stripSessionAssets` traverses children only when `type === "row"` (2389–2393). Reproduction: import `{"composition":{"slots":[{"type":"row","children":[{"type":"row","children":[{"type":"image","assetDataUrl":"SECRET"}]},{"type":"text"}]}]}}`; status reports successful import, nested row becomes a text leaf, and exported JSON still contains `SECRET`. Unsupported nested data should be rejected or normalized without preserving hidden descendants. This violates recursive session asset stripping after accepted import.

2. **Row validation is overwritten by imported raw fields.** `makeRowSlot` computes sanitized gap, alignment and breakpoint, then spreads `...overrides` after them (1624–1631); only count, ratios and children are subsequently protected. Import row `gap:-99, collapseAt:"bad", alignItems:"invalid"` with two text children. Import succeeds and JSON exports those exact invalid values; CSS exports negative gap and `badpx` breakpoint (2450–2452). No finite numeric/type validation occurs during hydration. Fractional `childCount:2.5` also throws invalid array length at 1776 rather than producing/rejecting a valid integer count deliberately.

3. **Failed import partially mutates the previous composition.** Import writes `state.canvasWidth` and `state.background` before hydrating slots (2465–2467). Fractional row count failure is caught, but those earlier assignments remain. In the browser reproduction without background, rejected import leaves old Asteria slots while exporting blank-preset background `#f5f1e8` instead of prior Asteria `#030409`. UI may still display the old rendering because rerender is later. Candidate state needs validation before assigning live state.

4. **Accepted malformed text role breaks CSS export.** Import a row with children `{"type":"text","role":12}` and a normal text child. Import reports success and renders. Export CSS throws `slot.role.toLowerCase is not a function`, with no CSS dialog generated. Raw leaf spread accepts role without type validation (1784–1786); `cssTokenName` assumes string (2415–2418). This issue also applies to top-level text roles.

## Existing requirements satisfied

- Old leaf-only JSON is accepted: importing `version:"0.1.0"` with `{type:"text",role:"Body",text:"legacy"}` hydrates missing typography controls, renders and exports valid `--font-body` tokens. Export version is correctly `0.1.1` (2399). Import intentionally has no version gate; arbitrary/missing versions are likewise not rejected (2462–2467). No supplied requirement demands rejecting future versions.
- Valid one-level row JSON preserves nested leaves, fills missing children to at least two, caps to four, refreshes IDs and clears image data URLs (1771–1780). Standard nested image reproduction retained `imageName:"x.svg"` but exported empty asset data. Counts and ratios are handled for valid integer inputs.
- Valid top-level and row-child images are stripped recursively by export (2389–2398). JSON serialization retains names and dimensions for reselection; no demand to persist binary images exists.
- CSS export includes row-child typography through `walkLeafSlots` (2420–2447), plus row gap, collapse and ratio tokens (2448–2453). Browser reproduction with two Body children exported both `--font-body` and `--font-body-2`. Scope is explicitly one row level.
- Source preserves PNG/SVG input acceptance and JPEG rejection: both allowed MIME and `.png`/`.svg` extension required (2329–2342). SVG uses an `img` source instead of injected markup (1920–1926). Live upload and decoder verification were not performed; preservation is source-confirmed only.

## Additional source concern

CSS deduplication counts only each base role name (2431–2436), so roles `Body`, `Body`, `Body-2` produce duplicate `--font-body-2` names; the third overwrites the second in CSS. This is deterministically implied by source, but not separately browser-reproduced here.

## Limits

Chromium probes used fresh pages for six import cases; no Firefox checks or image decoding/upload checks. Deep nesting is deliberately unsupported; the defect is retaining unsupported raw descendants and then exporting their assets, rather than absence of deep rendering support. No v0.2 feature requests inferred.
