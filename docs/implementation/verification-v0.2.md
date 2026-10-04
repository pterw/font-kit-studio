# v0.2.0 release-point verification — 2026-10-02

Gate evidence for the v0.2.0 release point. Nothing was changed to obtain it: the tree was clean before and after every gate, and this file is the only repository write.

## Artifact and environment

- Head: the PR #1 head at verification time; `git status --short` empty before and after all gates.
- Python 3.11.15; Node v22.22.0; Playwright (Python) 1.62.0; Chromium 141.0.7390.37 (`/opt/pw-browsers/chromium`, no `playwright install` run). Engines under test: Chromium only (`FKS_ENGINES=chromium`).
- SHA-256 (`sha256sum`):

| File | SHA-256 |
|---|---|
| `font_kit_studio_v0.1.1.html` | `0d75f19088b47df8ccde20443fcb334446ac6cc5d95f07d0151d40d9e42440ab` |
| `fontkit-bridge.js` | `005a88808221b2055d49848a3a91d3c1c2ad6c84a058a66a31871ad7aba4d6ce` |
| `scripts/serve.py` | `0ed0434298031c7f0f7815b958a5ca1d9dcd109fa85dab3d01609ae4d8567759` |
| `demo/index.html` | `692fac745970059c30495a681d09bcc5f88b372c2f7bf6e8496af98245240ed4` |

- The Studio file keeps its v0.1.1 filename. Provenance of the originally supplied v0.1.1 inputs is unchanged and passes (see output below).

## Scope

This verifies the v0.2.0 release point as built: live preview of a target page in Studio, the code view, sync of the generated overrides stylesheet, the arrange mode driven by the bridge protocol v1 manifest, the pop-out preview, and the free-font path, together with the preserved v0.1.1 responsive-row and Library behaviour. Evidence is the static checks, the full unittest/browser suite on Chromium, a JavaScript syntax check of the bridge, and a Studio plus demo smoke run.

## Exact commands

```bash
export FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
git rev-parse HEAD
git status --short
python3 --version
node --version
python3 -c "import playwright, importlib.metadata as m; print(m.version('playwright'))"
/opt/pw-browsers/chromium --version
python3 scripts/verify.py                # default full mode: static + provenance + full unittest suite
node --check fontkit-bridge.js
sha256sum font_kit_studio_v0.1.1.html fontkit-bridge.js scripts/serve.py demo/index.html
# smoke: python3 scripts/serve.py --studio-port <free> --target-port <free> --quiet,
# then Chromium (python playwright, executable_path=/opt/pw-browsers/chromium) opens
# <Studio URL>?target=<demo URL>, with fonts.googleapis.com routed to empty CSS
ps aux | grep serve.py
git status --short
```

## Gate results

| Gate | Result |
|---|---|
| Clean tree at the verified head | PASS (empty status) |
| `python3 scripts/verify.py` (static, provenance, full suite) | PASS, exit 0, 201 tests, OK |
| `node --check fontkit-bridge.js` | PASS, exit 0 |
| `sha256sum` of the four release files | recorded above |
| Studio and demo smoke (Chromium) | PASS |
| No leftover processes or files | PASS |

## Full verify.py output

Command run once: `python3 scripts/verify.py` (default full mode). Combined stdout and stderr, exit status 0. Two tests (`test_legacy_tokens_accept_only_safe_names_and_values`, `test_blocked_local_storage_does_not_stop_start_up_or_auto_connect`) print their docstring on the following line before `ok`; that is unittest verbose formatting, not a failure.

```text
PASS HTML IDs: 86 unique static IDs
PASS JavaScript syntax: 1 executable inline blocks
SHA-256 font_kit_studio_v0.1.1.html: 0d75f19088b47df8ccde20443fcb334446ac6cc5d95f07d0151d40d9e42440ab
PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
RUN unittest/browser tests
test_a_target_is_not_offered_itself_or_its_descendants_as_a_destination (test_bridge_runtime.ArrangementManifestTests.test_a_target_is_not_offered_itself_or_its_descendants_as_a_destination) ... ok
test_bulk_manifests_never_carry_siblings_or_containers (test_bridge_runtime.ArrangementManifestTests.test_bulk_manifests_never_carry_siblings_or_containers) ... ok
test_container_names_prefer_design_name_aria_label_heading_id_then_tag_class (test_bridge_runtime.ArrangementManifestTests.test_container_names_prefer_design_name_aria_label_heading_id_then_tag_class) ... ok
test_manifest_arrangement_describes_siblings_containers_and_capabilities (test_bridge_runtime.ArrangementManifestTests.test_manifest_arrangement_describes_siblings_containers_and_capabilities) ... ok
test_move_and_overlay_and_fonts_are_ignored_before_hello (test_bridge_runtime.ArrangementManifestTests.test_move_and_overlay_and_fonts_are_ignored_before_hello) ... ok
test_ready_and_targets_messages_grow_near_linearly_with_the_page (test_bridge_runtime.ArrangementManifestTests.test_ready_and_targets_messages_grow_near_linearly_with_the_page) ... ok
test_sibling_only_registrations_are_flagged_and_stay_addressable (test_bridge_runtime.ArrangementManifestTests.test_sibling_only_registrations_are_flagged_and_stay_addressable) ... ok
test_twenty_sections_of_a_hundred_targets_stay_near_linear (test_bridge_runtime.ArrangementManifestTests.test_twenty_sections_of_a_hundred_targets_stay_near_linear) ... ok
test_base64_svg_from_read_as_data_url_replaces_an_inline_svg_until_reset (test_bridge_runtime.AssetPlacementTests.test_base64_svg_from_read_as_data_url_replaces_an_inline_svg_until_reset) ... ok
test_only_png_and_svg_data_urls_are_placed (test_bridge_runtime.AssetPlacementTests.test_only_png_and_svg_data_urls_are_placed) ... ok
test_svg_payloads_never_execute_in_the_target (test_bridge_runtime.AssetPlacementTests.test_svg_payloads_never_execute_in_the_target) ... ok
test_an_app_that_rerenders_on_any_attribute_change_cannot_trap_the_bridge (test_bridge_runtime.AttributeWriteTests.test_an_app_that_rerenders_on_any_attribute_change_cannot_trap_the_bridge) ... ok
test_an_unchanged_style_or_attribute_value_is_never_rewritten (test_bridge_runtime.AttributeWriteTests.test_an_unchanged_style_or_attribute_value_is_never_rewritten) ... ok
test_auto_selectors_stay_unique_on_deep_repetitive_dom (test_bridge_runtime.AutoSelectorTests.test_auto_selectors_stay_unique_on_deep_repetitive_dom) ... ok
test_ledger_html_strips_bridge_state_from_nested_targets (test_bridge_runtime.ChangeLedgerTests.test_ledger_html_strips_bridge_state_from_nested_targets) ... ok
test_ledger_lists_changed_targets_with_selectors_and_cleaned_html (test_bridge_runtime.ChangeLedgerTests.test_ledger_lists_changed_targets_with_selectors_and_cleaned_html) ... ok
test_allowed_origins_attribute_restricts_who_can_say_hello (test_bridge_runtime.ConfirmedDefectTests.test_allowed_origins_attribute_restricts_who_can_say_hello) ... ok
test_clicks_are_not_intercepted_before_hello (test_bridge_runtime.ConfirmedDefectTests.test_clicks_are_not_intercepted_before_hello) ... ok
test_original_text_is_captured_once_across_rediscovery (test_bridge_runtime.ConfirmedDefectTests.test_original_text_is_captured_once_across_rediscovery) ... ok
test_restore_text_restores_original_text_without_throwing (test_bridge_runtime.ConfirmedDefectTests.test_restore_text_restores_original_text_without_throwing) ... ok
test_sibling_frame_cannot_open_or_hijack_the_session (test_bridge_runtime.ConfirmedDefectTests.test_sibling_frame_cannot_open_or_hijack_the_session) ... ok
test_wrong_session_or_protocol_version_is_ignored (test_bridge_runtime.ConfirmedDefectTests.test_wrong_session_or_protocol_version_is_ignored) ... ok
test_block_elements_cannot_go_into_inline_or_phrasing_parents (test_bridge_runtime.ContentModelGuardTests.test_block_elements_cannot_go_into_inline_or_phrasing_parents) ... ok
test_inline_into_inline_and_block_into_block_and_in_place_moves_are_allowed (test_bridge_runtime.ContentModelGuardTests.test_inline_into_inline_and_block_into_block_and_in_place_moves_are_allowed) ... ok
test_css_order_is_rejected_where_it_cannot_work (test_bridge_runtime.CssOrderTests.test_css_order_is_rejected_where_it_cannot_work) ... ok
test_css_order_strategy_records_order_declarations_without_touching_the_dom (test_bridge_runtime.CssOrderTests.test_css_order_strategy_records_order_declarations_without_touching_the_dom) ... ok
test_css_order_works_in_grids_and_is_not_blocked_by_framework_ownership (test_bridge_runtime.CssOrderTests.test_css_order_works_in_grids_and_is_not_blocked_by_framework_ownership) ... ok
test_font_stylesheets_are_allowed_on_any_target_kind (test_bridge_runtime.FontStylesheetTests.test_font_stylesheets_are_allowed_on_any_target_kind) ... ok
test_only_strictly_valid_font_stylesheet_urls_are_accepted (test_bridge_runtime.FontStylesheetTests.test_only_strictly_valid_font_stylesheet_urls_are_accepted) ... ok
test_stylesheets_are_injected_once_recorded_in_the_ledger_and_removed_by_reset (test_bridge_runtime.FontStylesheetTests.test_stylesheets_are_injected_once_recorded_in_the_ledger_and_removed_by_reset) ... ok
test_bridge_ready_carries_no_page_data_and_ready_describes_targets (test_bridge_runtime.HandshakeTests.test_bridge_ready_carries_no_page_data_and_ready_describes_targets) ... ok
test_first_hello_discovers_targets_once (test_bridge_runtime.HandshakeTests.test_first_hello_discovers_targets_once) ... ok
test_auto_init_opt_out_with_manual_init (test_bridge_runtime.InitOptionTests.test_auto_init_opt_out_with_manual_init) ... ok
test_constructed_instance_claims_the_global_slot (test_bridge_runtime.InitOptionTests.test_constructed_instance_claims_the_global_slot) ... ok
test_global_options_are_used_by_auto_init (test_bridge_runtime.InitOptionTests.test_global_options_are_used_by_auto_init) ... ok
test_only_real_data_urls_in_url_attributes_are_abbreviated (test_bridge_runtime.LedgerHtmlAttributeScopeTests.test_only_real_data_urls_in_url_attributes_are_abbreviated) ... ok
test_any_long_data_attribute_is_abbreviated_even_with_spaces_and_quotes (test_bridge_runtime.LedgerHtmlDataUrlTests.test_any_long_data_attribute_is_abbreviated_even_with_spaces_and_quotes) ... ok
test_long_data_urls_are_abbreviated_in_ledger_html (test_bridge_runtime.LedgerHtmlTests.test_long_data_urls_are_abbreviated_in_ledger_html) ... ok
test_composition_update_applies_slots_and_tokens_into_the_ledger (test_bridge_runtime.LegacyCompositionTests.test_composition_update_applies_slots_and_tokens_into_the_ledger) ... ok
test_legacy_tokens_accept_only_safe_names_and_values (test_bridge_runtime.LegacyCompositionTests.test_legacy_tokens_accept_only_safe_names_and_values)
One invalid token rejects the whole composition update: nothing is applied and nothing is acked as applied. ... ok
test_legacy_layout_reorder_is_recorded_in_structure_and_undone_by_reset_all (test_bridge_runtime.LegacyLayoutStructureTests.test_legacy_layout_reorder_is_recorded_in_structure_and_undone_by_reset_all) ... ok
test_form_controls_cannot_leave_their_form_owner (test_bridge_runtime.MoveGuardTests.test_form_controls_cannot_leave_their_form_owner) ... ok
test_framework_managed_subtrees_need_force_unless_css_order_is_used (test_bridge_runtime.MoveGuardTests.test_framework_managed_subtrees_need_force_unless_css_order_is_used) ... ok
test_label_and_aria_references_must_still_resolve_after_the_move (test_bridge_runtime.MoveGuardTests.test_label_and_aria_references_must_still_resolve_after_the_move) ... ok
test_radio_inputs_cannot_leave_their_group_but_can_reorder_inside_it (test_bridge_runtime.MoveGuardTests.test_radio_inputs_cannot_leave_their_group_but_can_reorder_inside_it) ... ok
test_children_the_app_adds_do_not_count_as_structural_changes (test_bridge_runtime.MoveTests.test_children_the_app_adds_do_not_count_as_structural_changes) ... ok
test_every_invalid_move_is_rejected_and_changes_nothing (test_bridge_runtime.MoveTests.test_every_invalid_move_is_rejected_and_changes_nothing) ... ok
test_ledger_structure_reports_changed_containers_and_reset_restores_the_order (test_bridge_runtime.MoveTests.test_ledger_structure_reports_changed_containers_and_reset_restores_the_order) ... ok
test_move_before_after_and_across_containers (test_bridge_runtime.MoveTests.test_move_before_after_and_across_containers) ... ok
test_move_by_index_reorders_the_dom_and_reports_the_canonical_move (test_bridge_runtime.MoveTests.test_move_by_index_reorders_the_dom_and_reports_the_canonical_move) ... ok
test_move_into_a_container_appends_by_default_or_goes_to_the_index (test_bridge_runtime.MoveTests.test_move_into_a_container_appends_by_default_or_goes_to_the_index) ... ok
test_reset_all_does_not_resurrect_children_the_app_removed (test_bridge_runtime.MoveTests.test_reset_all_does_not_resurrect_children_the_app_removed) ... ok
test_selectors_in_move_replies_describe_the_new_position (test_bridge_runtime.MoveTests.test_selectors_in_move_replies_describe_the_new_position) ... ok
test_in_target_overlay_is_opt_in_and_never_leaks_into_targets_or_html (test_bridge_runtime.OverlayOptionTests.test_in_target_overlay_is_opt_in_and_never_leaks_into_targets_or_html) ... ok
test_overlay_in_an_iframe_follows_the_same_rules (test_bridge_runtime.PopOutOverlayTests.test_overlay_in_an_iframe_follows_the_same_rules) ... ok
test_overlay_mode_draws_the_bridge_outline_and_removes_it_again (test_bridge_runtime.PopOutOverlayTests.test_overlay_mode_draws_the_bridge_outline_and_removes_it_again) ... ok
test_errors_outside_the_one_second_window_or_after_a_rejection_are_not_reported (test_bridge_runtime.RuntimeWarningTests.test_errors_outside_the_one_second_window_or_after_a_rejection_are_not_reported) ... ok
test_runtime_errors_after_an_update_or_move_are_reported_as_warnings (test_bridge_runtime.RuntimeWarningTests.test_runtime_errors_after_an_update_or_move_are_reported_as_warnings) ... ok
test_bounds_follow_scroll_and_size_changes_of_the_selected_target (test_bridge_runtime.SelectionTests.test_bounds_follow_scroll_and_size_changes_of_the_selected_target) ... ok
test_interact_mode_lets_the_page_behave_normally (test_bridge_runtime.SelectionTests.test_interact_mode_lets_the_page_behave_normally) ... ok
test_new_targets_are_announced_once_per_burst (test_bridge_runtime.SelectionTests.test_new_targets_are_announced_once_per_burst) ... ok
test_select_message_scrolls_target_into_view_and_highlight_is_select (test_bridge_runtime.SelectionTests.test_select_message_scrolls_target_into_view_and_highlight_is_select) ... ok
test_select_mode_reports_hover_changes_and_click_selects (test_bridge_runtime.SelectionTests.test_select_mode_reports_hover_changes_and_click_selects) ... ok
test_closed_opener_studio_stops_click_interception (test_bridge_runtime.SessionLifecycleTests.test_closed_opener_studio_stops_click_interception) ... ok
test_a_semantic_element_registered_as_a_sibling_first_is_an_ordinary_target (test_bridge_runtime.SiblingOnlyHitTestTests.test_a_semantic_element_registered_as_a_sibling_first_is_an_ordinary_target) ... ok
test_clicking_list_text_or_a_summary_does_not_select_the_wrapper (test_bridge_runtime.SiblingOnlyHitTestTests.test_clicking_list_text_or_a_summary_does_not_select_the_wrapper) ... ok
test_the_flag_and_the_hit_test_survive_rediscovery_moves_and_reconnects (test_bridge_runtime.SiblingOnlyHitTestTests.test_the_flag_and_the_hit_test_survive_rediscovery_moves_and_reconnects) ... ok
test_a_burst_of_rerenders_is_debounced_into_one_reapplication (test_bridge_runtime.SpaRobustnessTests.test_a_burst_of_rerenders_is_debounced_into_one_reapplication) ... ok
test_a_connected_auto_instance_is_not_replaced (test_bridge_runtime.SpaRobustnessTests.test_a_connected_auto_instance_is_not_replaced) ... ok
test_a_later_constructed_instance_replaces_an_unconnected_auto_instance (test_bridge_runtime.SpaRobustnessTests.test_a_later_constructed_instance_replaces_an_unconnected_auto_instance) ... ok
test_a_page_that_rerenders_on_every_style_change_cannot_trap_the_bridge_in_a_loop (test_bridge_runtime.SpaRobustnessTests.test_a_page_that_rerenders_on_every_style_change_cannot_trap_the_bridge_in_a_loop) ... ok
test_a_replaced_selected_target_stays_selected_and_an_auto_target_removal_clears (test_bridge_runtime.SpaRobustnessTests.test_a_replaced_selected_target_stays_selected_and_an_auto_target_removal_clears) ... ok
test_loading_the_script_twice_keeps_a_single_instance (test_bridge_runtime.SpaRobustnessTests.test_loading_the_script_twice_keeps_a_single_instance) ... ok
test_overrides_are_reapplied_when_a_rerender_replaces_the_element (test_bridge_runtime.SpaRobustnessTests.test_overrides_are_reapplied_when_a_rerender_replaces_the_element) ... ok
test_removing_the_selected_target_clears_the_selection (test_bridge_runtime.SpaRobustnessTests.test_removing_the_selected_target_clears_the_selection) ... ok
test_each_invalid_request_is_rejected_with_its_reason (test_bridge_runtime.TargetedUpdateTests.test_each_invalid_request_is_rejected_with_its_reason) ... ok
test_font_weight_snaps_to_declared_weights (test_bridge_runtime.TargetedUpdateTests.test_font_weight_snaps_to_declared_weights) ... ok
test_null_restores_the_original_inline_value (test_bridge_runtime.TargetedUpdateTests.test_null_restores_the_original_inline_value) ... ok
test_rejected_patch_changes_nothing (test_bridge_runtime.TargetedUpdateTests.test_rejected_patch_changes_nothing) ... ok
test_reset_one_target_or_everything (test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything) ... ok
test_revision_increments_by_exactly_one_per_successful_mutation (test_bridge_runtime.TargetedUpdateTests.test_revision_increments_by_exactly_one_per_successful_mutation) ... ok
test_text_edits_leaf_and_mixed_content_and_restore_text_keeps_styles (test_bridge_runtime.TargetedUpdateTests.test_text_edits_leaf_and_mixed_content_and_restore_text_keeps_styles) ... ok
test_update_canonicalizes_and_applies_important_inline_styles (test_bridge_runtime.TargetedUpdateTests.test_update_canonicalizes_and_applies_important_inline_styles) ... ok
test_fractional_child_counts (test_font_kit_studio_v011.BrowserCase.test_fractional_child_counts) ... ok
test_fractional_inspector_count_without_import (test_font_kit_studio_v011.BrowserCase.test_fractional_inspector_count_without_import) ... ok
test_malformed_row_values_are_normalized (test_font_kit_studio_v011.BrowserCase.test_malformed_row_values_are_normalized) ... ok
test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields (test_font_kit_studio_v011.BrowserCase.test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields) ... ok
test_row_controls_and_leaf_inspectors (test_font_kit_studio_v011.BrowserCase.test_row_controls_and_leaf_inspectors) ... ok
test_row_inspector_normalized_values_and_labels (test_font_kit_studio_v011.BrowserCase.test_row_inspector_normalized_values_and_labels) ... ok
test_task4_css_roles_are_valid_and_collision_free (test_font_kit_studio_v011.BrowserCase.test_task4_css_roles_are_valid_and_collision_free) ... ok
test_task4_css_slug_and_property_suffix_collisions (test_font_kit_studio_v011.BrowserCase.test_task4_css_slug_and_property_suffix_collisions) ... ok
test_task4_explicit_empty_kits_and_missing_field_compatibility (test_font_kit_studio_v011.BrowserCase.test_task4_explicit_empty_kits_and_missing_field_compatibility) ... ok
test_task4_failed_background_import_preserves_state (test_font_kit_studio_v011.BrowserCase.test_task4_failed_background_import_preserves_state) ... ok
test_task4_failed_import_is_transactional (test_font_kit_studio_v011.BrowserCase.test_task4_failed_import_is_transactional) ... ok
test_task4_image_upload_decode_rejection_and_selection_race (test_font_kit_studio_v011.BrowserCase.test_task4_image_upload_decode_rejection_and_selection_race) ... ok
test_task4_known_leaf_fields_have_safe_shapes (test_font_kit_studio_v011.BrowserCase.test_task4_known_leaf_fields_have_safe_shapes) ... ok
test_task4_recursive_asset_privacy_and_old_json_round_trip (test_font_kit_studio_v011.BrowserCase.test_task4_recursive_asset_privacy_and_old_json_round_trip) ... ok
test_task5_library_controls_and_mode_preservation (test_font_kit_studio_v011.BrowserCase.test_task5_library_controls_and_mode_preservation) ... ok
test_task5_offline_layouts_and_dynamic_ids (test_font_kit_studio_v011.BrowserCase.test_task5_offline_layouts_and_dynamic_ids) ... ok
test_unequal_child_alignment_geometry (test_font_kit_studio_v011.BrowserCase.test_unequal_child_alignment_geometry) ... ok
test_valid_row_factory_and_child_selection (test_font_kit_studio_v011.BrowserCase.test_valid_row_factory_and_child_selection) ... ok
test_weighted_columns_gaps_and_resize_observer_boundaries (test_font_kit_studio_v011.BrowserCase.test_weighted_columns_gaps_and_resize_observer_boundaries) ... ok
test_version_and_existing_model (test_font_kit_studio_v011.StructureTests.test_version_and_existing_model) ... ok
test_a_form_control_cannot_be_moved_out_of_its_form (test_live_integration.ArrangeTests.test_a_form_control_cannot_be_moved_out_of_its_form) ... ok
test_css_order_strategy_changes_the_look_but_not_the_dom (test_live_integration.ArrangeTests.test_css_order_strategy_changes_the_look_but_not_the_dom) ... ok
test_move_the_cta_next_shows_structure_in_the_html_tab_and_reset_undoes_it (test_live_integration.ArrangeTests.test_move_the_cta_next_shows_structure_in_the_html_tab_and_reset_undoes_it) ... ok
test_injecting_the_bridge_into_a_pop_out_connects_a_page_without_the_script_tag (test_live_integration.BookmarkletTests.test_injecting_the_bridge_into_a_pop_out_connects_a_page_without_the_script_tag) ... ok
test_the_readme_script_tag_loads_the_bridge_from_the_dev_server (test_live_integration.BookmarkletTests.test_the_readme_script_tag_loads_the_bridge_from_the_dev_server) ... ok
test_copy_uses_the_real_clipboard (test_live_integration.EditAndCodePanelTests.test_copy_uses_the_real_clipboard) ... ok
test_target_query_connects_and_clicking_the_page_edits_it (test_live_integration.EditAndCodePanelTests.test_target_query_connects_and_clicking_the_page_edits_it) ... ok
test_a_free_library_font_loads_its_stylesheet_in_the_target_and_the_synced_css (test_live_integration.FontTests.test_a_free_library_font_loads_its_stylesheet_in_the_target_and_the_synced_css) ... ok
test_imported_tokens_use_the_bridge_rule_and_reapply_settles_with_no_lingering_banner (test_live_integration.ImportedTokensTests.test_imported_tokens_use_the_bridge_rule_and_reapply_settles_with_no_lingering_banner) ... ok
test_select_mode_selects_links_and_interact_mode_follows_them (test_live_integration.InteractModeTests.test_select_mode_selects_links_and_interact_mode_follows_them) ... ok
test_the_instrumented_app_works_normally_without_studio (test_live_integration.InteractModeTests.test_the_instrumented_app_works_normally_without_studio) ... ok
test_studio_opened_as_a_file_edits_a_served_target_but_cannot_sync (test_live_integration.OpenedFromFileTests.test_studio_opened_as_a_file_edits_a_served_target_but_cannot_sync) ... ok
test_pop_out_edits_the_real_window_and_dock_returns_to_the_iframe (test_live_integration.PopOutTests.test_pop_out_edits_the_real_window_and_dock_returns_to_the_iframe) ... ok
test_studio_is_blocked_under_any_loopback_alias_or_path_case_but_other_ports_connect (test_live_integration.RecursionGuardTests.test_studio_is_blocked_under_any_loopback_alias_or_path_case_but_other_ports_connect) ... ok
test_restore_page_text_keeps_styles_and_reset_returns_the_page_byte_for_byte (test_live_integration.RestoreAndResetTests.test_restore_page_text_keeps_styles_and_reset_returns_the_page_byte_for_byte) ... ok
test_sync_writes_the_file_and_a_reload_keeps_the_style_and_asks_before_reapplying (test_live_integration.SyncAndReloadTests.test_sync_writes_the_file_and_a_reload_keeps_the_style_and_asks_before_reapplying) ... ok
test_demo_loads_from_target_port (test_preview_server.DemoPageTest.test_demo_loads_from_target_port) ... ok
test_demo_source_is_offline (test_preview_server.DemoPageTest.test_demo_source_is_offline) ... ok
test_no_sync_rejects_writes (test_preview_server.PreviewServerLifecycleTest.test_no_sync_rejects_writes) ... ok
test_prints_studio_url_and_shuts_down_cleanly (test_preview_server.PreviewServerLifecycleTest.test_prints_studio_url_and_shuts_down_cleanly) ... ok
test_refuses_overrides_outside_repo (test_preview_server.PreviewServerLifecycleTest.test_refuses_overrides_outside_repo) ... ok
test_write_failure_returns_json_500 (test_preview_server.PreviewServerLifecycleTest.test_write_failure_returns_json_500) ... ok
test_both_ports_serve_repo_files (test_preview_server.PreviewServerTest.test_both_ports_serve_repo_files) ... ok
test_dot_paths_are_not_served (test_preview_server.PreviewServerTest.test_dot_paths_are_not_served) ... ok
test_hidden_check_uses_the_served_path (test_preview_server.PreviewServerTest.test_hidden_check_uses_the_served_path) ... ok
test_host_header_allow_list (test_preview_server.PreviewServerTest.test_host_header_allow_list) ... ok
test_missing_overrides_is_empty_css_on_both_ports (test_preview_server.PreviewServerTest.test_missing_overrides_is_empty_css_on_both_ports) ... ok
test_put_rejects_foreign_origin (test_preview_server.PreviewServerTest.test_put_rejects_foreign_origin) ... ok
test_put_requires_css_content_type (test_preview_server.PreviewServerTest.test_put_requires_css_content_type) ... ok
test_put_size_limit (test_preview_server.PreviewServerTest.test_put_size_limit) ... ok
test_put_writes_exact_bytes_atomically (test_preview_server.PreviewServerTest.test_put_writes_exact_bytes_atomically) ... ok
test_root_redirects (test_preview_server.PreviewServerTest.test_root_redirects) ... ok
test_status_endpoint_on_studio_port (test_preview_server.PreviewServerTest.test_status_endpoint_on_studio_port) ... ok
test_target_port_has_no_fontkit_endpoints (test_preview_server.PreviewServerTest.test_target_port_has_no_fontkit_endpoints) ... ok
test_alt_arrow_shortcuts_only_apply_in_the_target_view_and_never_inside_text_fields (test_studio_live.StudioArrangeTests.test_alt_arrow_shortcuts_only_apply_in_the_target_view_and_never_inside_text_fields) ... ok
test_bulk_manifests_and_arrangement_only_targets (test_studio_live.StudioArrangeTests.test_bulk_manifests_and_arrangement_only_targets) ... ok
test_css_order_moves_persist_in_live_json_and_reapply_after_a_reload (test_studio_live.StudioArrangeTests.test_css_order_moves_persist_in_live_json_and_reapply_after_a_reload) ... ok
test_css_order_strategy_toggle_and_framework_default (test_studio_live.StudioArrangeTests.test_css_order_strategy_toggle_and_framework_default) ... ok
test_framework_guard_offers_move_anyway_and_other_guards_do_not (test_studio_live.StudioArrangeTests.test_framework_guard_offers_move_anyway_and_other_guards_do_not) ... ok
test_html_tab_shows_structure_and_css_tab_points_to_it (test_studio_live.StudioArrangeTests.test_html_tab_shows_structure_and_css_tab_points_to_it) ... ok
test_move_buttons_send_design_move_and_the_target_reorders (test_studio_live.StudioArrangeTests.test_move_buttons_send_design_move_and_the_target_reorders) ... ok
test_move_into_another_container (test_studio_live.StudioArrangeTests.test_move_into_another_container) ... ok
test_move_retries_a_revision_conflict_once (test_studio_live.StudioArrangeTests.test_move_retries_a_revision_conflict_once) ... ok
test_narrow_layout_with_arrange_guard_and_popout_has_no_overflow (test_studio_live.StudioArrangeTests.test_narrow_layout_with_arrange_guard_and_popout_has_no_overflow) ... ok
test_reapply_clears_a_target_css_order_that_studio_no_longer_saves (test_studio_live.StudioArrangeTests.test_reapply_clears_a_target_css_order_that_studio_no_longer_saves) ... ok
test_reapply_is_transactional_when_the_follow_up_is_rejected (test_studio_live.StudioArrangeTests.test_reapply_is_transactional_when_the_follow_up_is_rejected) ... ok
test_reapply_of_a_non_library_family_releases_the_stylesheet (test_studio_live.StudioArrangeTests.test_reapply_of_a_non_library_family_releases_the_stylesheet) ... ok
test_reapply_replays_a_partial_saved_order_group_after_the_reset (test_studio_live.StudioArrangeTests.test_reapply_replays_a_partial_saved_order_group_after_the_reset) ... ok
test_reapply_replays_font_stylesheets_and_clears_stale_orders (test_studio_live.StudioArrangeTests.test_reapply_replays_font_stylesheets_and_clears_stale_orders) ... ok
test_reapply_states_that_it_resets_a_dom_moved_arrangement (test_studio_live.StudioArrangeTests.test_reapply_states_that_it_resets_a_dom_moved_arrangement) ... ok
test_runtime_warnings_reach_the_status_area_and_code_panel_as_text (test_studio_live.StudioArrangeTests.test_runtime_warnings_reach_the_status_area_and_code_panel_as_text) ... ok
test_sibling_list_escapes_names_supports_keyboard_and_drag_and_drop (test_studio_live.StudioArrangeTests.test_sibling_list_escapes_names_supports_keyboard_and_drag_and_drop) ... ok
test_blocked_local_storage_does_not_stop_start_up_or_auto_connect (test_studio_live.StudioBlockedStorageTests.test_blocked_local_storage_does_not_stop_start_up_or_auto_connect)
Browsers that block site data throw on the localStorage getter; Studio must render and connect anyway. ... ok
test_connect_does_not_broadcast_composition_or_restyle_target (test_studio_live.StudioDefectTests.test_connect_does_not_broadcast_composition_or_restyle_target) ... ok
test_send_path_has_single_anti_recursion_guard_and_never_posts_to_parent (test_studio_live.StudioDefectTests.test_send_path_has_single_anti_recursion_guard_and_never_posts_to_parent) ... ok
test_spoofed_messages_from_foreign_window_or_session_are_ignored (test_studio_live.StudioDefectTests.test_spoofed_messages_from_foreign_window_or_session_are_ignored) ... ok
test_a_text_overrides_compare_like_the_trimmed_bridge_ledger (test_studio_live.StudioFixRound1Tests.test_a_text_overrides_compare_like_the_trimmed_bridge_ledger) ... ok
test_b_design_targets_replaces_the_target_list (test_studio_live.StudioFixRound1Tests.test_b_design_targets_replaces_the_target_list) ... ok
test_c1_target_url_scheme_allow_list (test_studio_live.StudioFixRound1Tests.test_c1_target_url_scheme_allow_list) ... ok
test_c_live_import_rejects_values_css_would_reject (test_studio_live.StudioFixRound1Tests.test_c_live_import_rejects_values_css_would_reject) ... ok
test_every_control_message_carries_protocol_version_and_session (test_studio_live.StudioFixRound1Tests.test_every_control_message_carries_protocol_version_and_session) ... ok
test_i1_keystroke_numeric_entry_applies_typed_values (test_studio_live.StudioFixRound1Tests.test_i1_keystroke_numeric_entry_applies_typed_values) ... ok
test_i2_studio_overrides_are_persisted_and_accept_is_explicit (test_studio_live.StudioFixRound1Tests.test_i2_studio_overrides_are_persisted_and_accept_is_explicit) ... ok
test_i3_every_iframe_load_regreets_both_announce_orders (test_studio_live.StudioFixRound1Tests.test_i3_every_iframe_load_regreets_both_announce_orders) ... ok
test_i4_reload_that_loses_composition_tokens_raises_banner_not_a_smaller_file (test_studio_live.StudioFixRound1Tests.test_i4_reload_that_loses_composition_tokens_raises_banner_not_a_smaller_file) ... ok
test_m3_late_applied_after_timeout_updates_canonical_state (test_studio_live.StudioFixRound1Tests.test_m3_late_applied_after_timeout_updates_canonical_state) ... ok
test_m3_late_reset_reply_reselects_like_the_normal_path (test_studio_live.StudioFixRound1Tests.test_m3_late_reset_reply_reselects_like_the_normal_path) ... ok
test_composer_loads_the_families_it_uses_and_load_free_fonts_loads_all (test_studio_live.StudioFreeFontTests.test_composer_loads_the_families_it_uses_and_load_free_fonts_loads_all) ... ok
test_composition_presets_use_free_families_and_legacy_keys_still_import (test_studio_live.StudioFreeFontTests.test_composition_presets_use_free_families_and_legacy_keys_still_import) ... ok
test_defaults_are_free_and_adobe_is_an_opt_in_with_an_empty_field (test_studio_live.StudioFreeFontTests.test_defaults_are_free_and_adobe_is_an_opt_in_with_an_empty_field) ... ok
test_library_has_sixteen_free_families_loaded_on_demand (test_studio_live.StudioFreeFontTests.test_library_has_sixteen_free_families_loaded_on_demand) ... ok
test_live_family_selection_sends_font_stylesheet_and_css_starts_with_import (test_studio_live.StudioFreeFontTests.test_live_family_selection_sends_font_stylesheet_and_css_starts_with_import) ... ok
test_offline_loading_never_hangs_or_throws (test_studio_live.StudioFreeFontTests.test_offline_loading_never_hangs_or_throws) ... ok
test_live_field_export_import_round_trip_and_transactional_rejection (test_studio_live.StudioPersistenceTests.test_live_field_export_import_round_trip_and_transactional_rejection) ... ok
test_narrow_target_view_has_no_horizontal_overflow (test_studio_live.StudioPersistenceTests.test_narrow_target_view_has_no_horizontal_overflow) ... ok
test_reconnect_banner_reapply_and_accept (test_studio_live.StudioPersistenceTests.test_reconnect_banner_reapply_and_accept) ... ok
test_blocked_popup_keeps_the_iframe (test_studio_live.StudioPopoutTests.test_blocked_popup_keeps_the_iframe) ... ok
test_closing_the_popup_reports_disconnected_and_dock_recovers (test_studio_live.StudioPopoutTests.test_closing_the_popup_reports_disconnected_and_dock_recovers) ... ok
test_iframe_mode_sends_overlay_false_and_dock_returns_to_it (test_studio_live.StudioPopoutTests.test_iframe_mode_sends_overlay_false_and_dock_returns_to_it) ... ok
test_pop_out_accepts_only_the_popup_at_the_expected_origin (test_studio_live.StudioPopoutTests.test_pop_out_accepts_only_the_popup_at_the_expected_origin) ... ok
test_pop_out_opens_the_named_window_and_the_inspector_edits_it (test_studio_live.StudioPopoutTests.test_pop_out_opens_the_named_window_and_the_inspector_edits_it) ... ok
test_pop_out_validates_the_url_before_window_open (test_studio_live.StudioPopoutTests.test_pop_out_validates_the_url_before_window_open) ... ok
test_code_panel_css_html_json_copy_and_download (test_studio_live.StudioProtocolTests.test_code_panel_css_html_json_copy_and_download) ... ok
test_explicit_composition_sync_is_session_gated (test_studio_live.StudioProtocolTests.test_explicit_composition_sync_is_session_gated) ... ok
test_handshake_status_badges_and_target_query (test_studio_live.StudioProtocolTests.test_handshake_status_badges_and_target_query) ... ok
test_live_inspector_seeds_from_computed_and_respects_editable (test_studio_live.StudioProtocolTests.test_live_inspector_seeds_from_computed_and_respects_editable) ... ok
test_no_bridge_detected_after_timeout (test_studio_live.StudioProtocolTests.test_no_bridge_detected_after_timeout) ... ok
test_restore_page_text_uses_session (test_studio_live.StudioProtocolTests.test_restore_page_text_uses_session) ... ok
test_revision_conflict_is_retried_once (test_studio_live.StudioProtocolTests.test_revision_conflict_is_retried_once) ... ok
test_select_interact_toggle_and_studio_owned_overlay (test_studio_live.StudioProtocolTests.test_select_interact_toggle_and_studio_owned_overlay) ... ok
test_single_in_flight_request_coalesces_pending_patches (test_studio_live.StudioProtocolTests.test_single_in_flight_request_coalesces_pending_patches) ... ok
test_sync_and_debounced_serialized_auto_sync (test_studio_live.StudioProtocolTests.test_sync_and_debounced_serialized_auto_sync) ... ok
test_sync_disabled_under_file_url (test_studio_live.StudioProtocolTests.test_sync_disabled_under_file_url) ... ok
test_targeted_updates_canonical_values_and_rejection_reseed (test_studio_live.StudioProtocolTests.test_targeted_updates_canonical_values_and_rejection_reseed) ... ok
test_only_studio_itself_is_blocked_not_every_url_that_mentions_it (test_studio_live.StudioRecursionGuardTests.test_only_studio_itself_is_blocked_not_every_url_that_mentions_it) ... ok
test_invalid_saved_tokens_reject_the_whole_import (test_studio_live.StudioSavedTokensTests.test_invalid_saved_tokens_reject_the_whole_import) ... ok
test_saved_composition_tokens_round_trip_through_the_live_json (test_studio_live.StudioSavedTokensTests.test_saved_composition_tokens_round_trip_through_the_live_json) ... ok
test_ledger_tokens_and_imports_follow_the_bridge_rules (test_studio_live.StudioSharedRulesTests.test_ledger_tokens_and_imports_follow_the_bridge_rules) ... ok

----------------------------------------------------------------------
Ran 201 tests in 331.374s

OK
PASS unittest/browser tests
```

## Test count per file

Parsed from the verbose unittest output above (each result line grouped by its module).

| Test file | Tests |
|---|---:|
| `tests/test_bridge_runtime.py` | 83 |
| `tests/test_font_kit_studio_v011.py` | 20 |
| `tests/test_live_integration.py` | 16 |
| `tests/test_preview_server.py` | 18 |
| `tests/test_studio_live.py` | 64 |
| **Total** | **201** |

This matches `Ran 201 tests in 331.374s`, `OK`; no failures, errors or skips reported.

## Smoke results

`python3 scripts/serve.py --studio-port 44985 --target-port 58181 --quiet` (ports chosen free at run time) printed the Studio URL `http://localhost:44985/font_kit_studio_v0.1.1.html?target=http://localhost:58181/demo/`. Chromium opened that URL with `fonts.googleapis.com` routed to an empty CSS response. The server was stopped in a `finally` block.

| Viewport | "Connected" shown | documentElement scrollWidth / clientWidth | Horizontal overflow | Console errors | Page errors |
|---|---|---|---|---|---|
| 1440×900 | yes | 1440 / 1440 | none | none | none |
| 390×844 | yes | 390 / 390 | none | none | none |

After the run, `ps aux | grep serve.py` showed no process and `git status --short` was empty (no stray overrides stylesheet or other files).

## Limits

- Firefox is not installed in this environment, so only Chromium was run (D010). Gecko behaviour for v0.2.0 is unverified here; the first Firefox run is expected in CI.
- Framework recipes are illustrative and were not executed against real framework projects.
- No physical devices were used; the 1440×900 and 390×844 checks are Chromium viewport emulation.
- Chromium here is 141.0.7390.37 with Playwright 1.62.0, so results are not directly comparable with the v0.1.1 baseline browser versions.
- The smoke run covers connection and layout at two viewports with the bundled demo page, not every v0.2.0 interaction; those are covered by the unittest/browser suite.

# v0.2.1 PR A release-point verification — 2026-10-03

Gate evidence for the first v0.2.1 pull request (fit-and-finish, behaviour: plan Tasks 1-5, 4b and A6). Nothing was changed to obtain it: the tree was clean before and after every gate.

## Artifact and environment

- Head: `0f410c0` on the PR A branch; `git status --short` empty before and after all gates.
- Python 3.11.15; Node v22.22.0; Playwright (Python) 1.62.0; Chromium 141.0.7390.37 (`/opt/pw-browsers/chromium`, no `playwright install` run). Engines under test: Chromium only (`FKS_ENGINES=chromium`).
- SHA-256 (`sha256sum`):

| File | SHA-256 |
|---|---|
| `font_kit_studio_v0.1.1.html` | `0d907228ee90b1cc268e0039548e8fbd882a984a994215cbbcbf112f38c758d6` |
| `fontkit-bridge.js` | `a91551238cdab1d626eb70256c75e2650c23a2ca8d7e06808452a5bed110cd69` |
| `scripts/serve.py` | `706f10cc9b2970edba1800ee2d4dbb6b2db49cfe1b271894733b1df5ccd9ef71` |
| `demo/index.html` | `ba7b03ef74439de192c3ecce3a12ab6e2b728cd16f914d0e8f36a631fd19b951` |

## Exact commands

```bash
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
node --check fontkit-bridge.js
python -m unittest discover -s tests
python scripts/dev/frontend_gate.py --offline
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
```

## Gate results

| Gate | Result |
|---|---|
| Static checks and provenance | PASS (unique IDs, inline JS syntax, three `supplied-v0.1.1` blobs match `SOURCES.json`) |
| Bridge syntax (`node --check`) | OK |
| Full unittest/browser suite, Chromium | `Ran 623 tests in 740.902s`, `OK` |
| Frontend gate, offline | `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines, 0 FAIL lines` |
| Commit messages | `OK: 13 commits checked` |

The one skipped blocking run is the free-fonts load check, which needs the network and is skipped by design under `--offline`. The 140 REPORT lines are advisory measurements (touch targets under 44 px in the wide-touch profile, for example `#liveReapply` at 160x30); they do not fail the build (D029) and are input for PR B's controls pass.

The suite printed one `TargetClosedError` line to stderr. It is a Playwright future left pending when a page in `tests/test_studio_first_run.py` closes during teardown; it was already seen in that module's review and does not fail or skip any test.

## Test count per file

Counted with the unittest loader at the same head.

| Test file | Tests |
|---|---:|
| `tests/test_bridge_runtime.py` | 128 |
| `tests/test_commit_messages.py` | 21 |
| `tests/test_font_kit_studio_v011.py` | 20 |
| `tests/test_frontend_gate_fonts.py` | 6 |
| `tests/test_frontend_gate_helpers.py` | 62 |
| `tests/test_frontend_gate_report.py` | 35 |
| `tests/test_frontend_gate_runner.py` | 56 |
| `tests/test_frontend_gate_theme_browser.py` | 2 |
| `tests/test_live_integration.py` | 43 |
| `tests/test_preview_server.py` | 34 |
| `tests/test_studio_first_run.py` | 22 |
| `tests/test_studio_import_link.py` | 16 |
| `tests/test_studio_live.py` | 152 |
| `tests/test_studio_review_findings.py` | 11 |
| `tests/test_studio_stage.py` | 11 |
| `tests/test_support.py` | 4 |
| **Total** | **623** |

## Limits

- Firefox is not installed here; it runs in CI and is advisory (D029). Gecko behaviour for these changes is unverified locally.
- Phone and touch layouts were measured by the frontend gate's advisory profiles only; no physical devices were used.
- The free-fonts load path was not exercised (offline gate); the suite covers it with routed font responses.
- Windows port reuse in `scripts/serve.py` is checked by code reading only.

# v0.2.1 PR B release-point verification — 2026-10-04

Gate evidence for the second v0.2.1 pull request (PR #5: plan Tasks T0, B0 and 6-9, that is the shared test browser, the late-reply import fix, controls disabled with a reason, dead controls, the visual pass and the README). Nothing was changed to obtain it: the tree was clean before and after every gate.

## Artifact and environment

- Head: `72d2a34` (`72d2a345c8158f22f4e7c0bbd1a5aaf23594c4d5`, "docs: bring the README and screenshots up to date with v0.2.1") on the PR B branch; `git status --porcelain` empty before and after every gate. `origin/main` is `ffcab4f`, the merge of PR A; no fetch was run.
- Python 3.11.15; Node v22.22.0; Playwright (Python) 1.62.0; Chromium 141.0.7390.37 (`/opt/pw-browsers/chromium`, no `playwright install` run). Engines under test: Chromium only (`FKS_ENGINES=chromium`). The container has 4 CPUs; timings are wall clock, so compare them loosely.
- SHA-256 (`sha256sum`):

| File | SHA-256 |
|---|---|
| `font_kit_studio_v0.1.1.html` | `950dbc00cff1ee9b6d843a7a29cdc46f76f547acd17e723093df7887c86b15ff` |
| `fontkit-bridge.js` | `a91551238cdab1d626eb70256c75e2650c23a2ca8d7e06808452a5bed110cd69` |
| `scripts/serve.py` | `133aeb4ce2f50834818e448b89bca3c7414c518e11b23cd670ea4f2141440bf8` |
| `demo/index.html` | `52e7404650610215431767cb384c60ac1945e7276bec15cac938c84c67868882` |

`fontkit-bridge.js` has the same hash as in the PR A section: PR B leaves the bridge unchanged.

## Exact commands

```bash
export FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
git rev-parse HEAD
git status --porcelain
python scripts/verify.py --static-only
node --version
node --check fontkit-bridge.js
python -m unittest discover -s tests -v
python scripts/dev/frontend_gate.py --offline --engines chromium
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
sha256sum font_kit_studio_v0.1.1.html fontkit-bridge.js scripts/serve.py demo/index.html
git status --porcelain
```

Each gate ran once, in this order, on the head above. None was repeated.

## Gate results

| Gate | Result |
|---|---|
| Clean tree at the verified head | PASS (empty status before and after every gate) |
| Static checks and provenance (`python scripts/verify.py --static-only`) | PASS, exit 0: 96 unique static IDs, 1 inline JavaScript block parses, the three `supplied-v0.1.1` blobs match `SOURCES.json` |
| Bridge syntax (`node --check fontkit-bridge.js`, Node v22.22.0) | PASS, exit 0, no output |
| Full unittest/browser suite, Chromium (`python -m unittest discover -s tests -v`) | PASS, exit 0: `Ran 786 tests in 655.691s`, `OK` |
| Frontend gate, offline, Chromium (`python scripts/dev/frontend_gate.py --offline --engines chromium`) | PASS, exit 0: `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 166 REPORT lines, 1 SKIP lines, 0 FAIL lines` |
| Commit messages (`python scripts/dev/check_commit_messages.py --range origin/main..HEAD`) | PASS, exit 0: `commit-message check: OK: 20 commits checked` (PR B's 20 commits) |
| Firefox canary | NOT RUN locally: no Firefox build exists here; CI runs it (D037) |
| Leftover processes and files | None: no `serve.py`, test or browser process after the gates, `git status --porcelain` empty, and the git-ignored paths are the same as before |

## Static check output

Command: `python scripts/verify.py --static-only`, exit 0. The last line is the flag's own message: the suite ran as its own gate below.

```text
PASS HTML IDs: 96 unique static IDs
PASS JavaScript syntax: 1 executable inline blocks
SHA-256 font_kit_studio_v0.1.1.html: 950dbc00cff1ee9b6d843a7a29cdc46f76f547acd17e723093df7887c86b15ff
PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
SKIP unittest/browser tests: --static-only; full acceptance not checked
```

## Test count and suite time

`python -m unittest discover -s tests -v` printed `Ran 786 tests in 655.691s` and `OK`, exit 0. Wall clock was 2026-10-04T04:18:14Z to 04:29:10Z.

| Measure | PR A (`0f410c0`) | PR B (`72d2a34`) |
|---|---:|---:|
| Tests | 623 | 786 (+163) |
| Suite time | 740.902s | 655.691s |

Of the 163 added tests, 13 arrived with the commits that landed on PR A after `0f410c0` (636 tests at `origin/main`, counted with the unittest loader on `git archive origin/main`), and 150 are PR B's.

All 786 result lines end `ok`. There are no failures, errors, skips, expected failures or unexpected successes. 69 tests carry a docstring and print their id and docstring on two lines; that is unittest's verbose format, not a failure. The combined stdout and stderr hold only the unittest report: the stray `TargetClosedError` line recorded for PR A did not appear.

Counted with the unittest loader at the same head; the per-file counts parsed from the verbose output are identical.

| Test file | PR A | PR B | Change |
|---|---:|---:|---:|
| `tests/test_bridge_runtime.py` | 128 | 128 | 0 |
| `tests/test_commit_messages.py` | 21 | 21 | 0 |
| `tests/test_font_kit_studio_v011.py` | 20 | 20 | 0 |
| `tests/test_frontend_gate_fonts.py` | 6 | 6 | 0 |
| `tests/test_frontend_gate_helpers.py` | 62 | 62 | 0 |
| `tests/test_frontend_gate_report.py` | 35 | 35 | 0 |
| `tests/test_frontend_gate_runner.py` | 56 | 56 | 0 |
| `tests/test_frontend_gate_theme_browser.py` | 2 | 2 | 0 |
| `tests/test_live_integration.py` | 43 | 52 | +9 |
| `tests/test_preview_server.py` | 34 | 34 | 0 |
| `tests/test_studio_controls.py` | 0 | 32 | +32 (new file) |
| `tests/test_studio_dead_controls.py` | 0 | 26 | +26 (new file) |
| `tests/test_studio_first_run.py` | 22 | 24 | +2 |
| `tests/test_studio_import_link.py` | 16 | 46 | +30 |
| `tests/test_studio_live.py` | 152 | 152 | 0 |
| `tests/test_studio_review_findings.py` | 11 | 12 | +1 |
| `tests/test_studio_stage.py` | 11 | 11 | 0 |
| `tests/test_studio_visual.py` | 0 | 33 | +33 (new file) |
| `tests/test_support.py` | 4 | 34 | +30 |
| **Total** | **623** | **786** | **+163** |

## Frontend gate

Command: `python scripts/dev/frontend_gate.py --offline --engines chromium`, exit 0, 18 seconds (2026-10-04T04:30:04Z to 04:30:22Z). 15 runs were planned and all 15 finished: 7 blocking runs (desktop Chromium) and 8 advisory runs (mobile and wide touch). The one skipped blocking run is the free-fonts load check, which needs the network and is skipped by design under `--offline`. Output without the REPORT lines:

```text
[frontend_gate] engines: chromium; planned runs: 15; blocking: chromium:desktop
[frontend_gate] PASS network isolation [desktop, chromium]
[frontend_gate] SKIP free fonts load [desktop, chromium]: skipped by --offline: this check needs fonts.googleapis.com
[frontend_gate] PASS no horizontal overflow [desktop, chromium]
[frontend_gate] PASS no horizontal overflow [mobile, chromium]
[frontend_gate] PASS no horizontal overflow [wide touch, chromium]
[frontend_gate] PASS initial visibility [desktop, chromium]
[frontend_gate] PASS initial visibility [mobile, chromium]
[frontend_gate] PASS live edit [desktop, chromium]
[frontend_gate] PASS live edit [mobile, chromium]
[frontend_gate] PASS live edit [wide touch, chromium]
[frontend_gate] PASS logo paint [desktop, chromium]
[frontend_gate] PASS theme contrast [desktop, chromium]
[frontend_gate] PASS theme contrast [mobile, chromium]
[frontend_gate] PASS touch targets [mobile, chromium]
[frontend_gate] PASS touch targets [wide touch, chromium]
[frontend_gate] SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 166 REPORT lines, 1 SKIP lines, 0 FAIL lines
```

The 166 REPORT lines are all `touch targets` measurements of controls whose smaller side is under 44 px. They are advisory and do not fail the build (D029). Grouped by profile:

| Profile | REPORT lines |
|---|---:|
| desktop | 0 |
| mobile | 82 |
| wide touch | 84 |
| **Total** | **166** |

By surface (a line can name one control or a group of the same control, for example `li.live-sibling` with "4 of them"):

| Surface | Mobile | Wide touch |
|---|---:|---:|
| Composer specimen | 39 | 39 |
| Composer Live App view, title selected | 25 | 25 |
| Studio Library | 11 | 11 |
| Composer reconnect banner | 3 | 3 |
| Demo (standalone) | 4 | 6 |
| **Total** | **82** | **84** |

PR A recorded 140 REPORT lines; this head has 166 (+26). The PR A section named the wide-touch profile only and did not split the 140 by profile, so a per-profile comparison is not possible. `button#liveReapply` is still listed, at 176x28 (PR A: 160x30). Between the two heads the gate's own code changed only in label wording (the page is now called Live App), so the measuring is the same and the difference comes from the pages it measures.

## What was not run

- Firefox canary (`PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v`): not run locally. No Firefox build exists in this environment: none is on the path, `/opt/pw-browsers` holds only Chromium, its headless shell and ffmpeg, `FKS_FIREFOX_EXECUTABLE` is not set, and the path Playwright expects (`/opt/pw-browsers/firefox-1538/firefox/firefox`) is missing. No browser was downloaded. CI runs the canary and the gate's Firefox runs as advisory checks (D037, D029). Gecko behaviour of PR B is unverified here.
- The gate's Firefox runs: the gate ran with `--engines chromium`, so none of its Firefox runs happened.
- The free-fonts load check against the real font host: skipped by `--offline`. The suite's free-font tests ran, with routed font responses.
- Physical devices: none were used. The mobile and wide-touch profiles are Chromium viewport emulation.
- `python scripts/verify.py` in its default full mode as a single command: not run as such. Its static half ran as `--static-only` and the suite ran as `unittest discover`.
