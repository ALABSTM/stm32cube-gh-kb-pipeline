# Manual Upload Folder (Files JSON Split)

This folder is dedicated to manual datasource uploads (no API).

## Goal

Split heavy ST-ready files JSON payloads into smaller parts, then upload these parts manually in ST datasource UI.

## Generate split parts

From repository root:

PowerShell:
python -m pipeline.delivery.split_st_ready_files_for_manual_upload --clean-output

Or with helper script:
./pipeline_Automation/Prepare_Manual_Files_Splits.ps1 -CleanOutput

Target exactly 50 parts for STM32CubeH7 (recommended when current split is too fragmented):
./pipeline_Automation/Prepare_Manual_Files_Splits.ps1 -OutputDir datasets/07_delivery/st_ready/manual_upload/files_json_split_tuned -Pattern st_ready_files_stm32cubeh7.json -SplitAll -CleanOutput -TargetParts 50 -MaxPayloadKB 0

Notes:
- MaxPayloadKB 0 disables payload-size cap and keeps the split at the requested part count.
- If MaxPayloadKB is set to a positive value, the splitter can create more than 50 parts to respect payload limits.

Default output folder:
- datasets/07_delivery/st_ready/manual_upload/files_json_split

## Manual datasource settings (Files datasource)

- Root Tag Path: files
- Preferred Link URL Template: {{github_url}}
- Link Label Template: {{path}}

Alternative URL template if placeholder expansion is required:
- https://github.com/STMicroelectronics/{{repo}}/{{root_dir}}/{{root_ref}}/{{path_url}}

Important:
- Do not use {{root_path}} in Link URL Template.
- Some indexers URL-encode placeholder values and transform blob/master into blob%2Fmaster, which yields broken links.

## Upload order

1. Open one repo folder inside files_json_split.
2. Upload part files in index order:
   - st_ready_files_<repo>__part001.json
   - st_ready_files_<repo>__part002.json
   - ...
3. Validate indexing status before next repo.
4. Keep summary file for traceability:
   - summary_st_ready_files_<repo>__manual_split.json

## Manifest

A global manifest is written at:
- datasets/07_delivery/st_ready/manual_upload/files_json_split/summary_manual_split_files_json.json

It includes:
- source files processed/skipped/errors
- split rules
- generated part counts
