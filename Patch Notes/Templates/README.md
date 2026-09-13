# Current patch notes templates

Replace bracketed placeholders with verified extraction content. Each HTML is standalone with embedded fonts/logo and a native 2560×1440 canvas. Capture matching PNGs at device scale factor 1 after window.renderReady.

- economy_template.html: Shop Rotations only. Preserve column width/type; right half is for a character.
- monthly_characters_traits_template.html: faction, then character, then ability changes.
- monthly_guild_raids_template.html: grouped boss/enemy changes.
- monthly_crusade_modes_template.html: Operations & Vault nested in Crusade; Other Modes below.
- bugfixes_template.html: stacked sections, alphabetical subjects within each.

Content stays left. Reserve right space approximately x=1740 to 2460, y=270 to 1340 (Economy leaves more). Keep original header, no category subtitle. Use compact player-facing copy; do not spread short topics across many slides.

Validate populated files for clipping, missing assets, heading collisions and portrait-space intrusion. Export one 2560×1440 PNG per final HTML and ZIP the set. Never deliver the bracketed placeholders as a finished patch.

Approved populated examples: V1.42/V1.42_Header_Restored. Calendar, Requisitions and Character Card designs were not modified in this consolidation. Follow PATCH_NOTES_TEMPLATE_INSTRUCTIONS.md for sourcing, cadence, extraction and remaining slide types.
