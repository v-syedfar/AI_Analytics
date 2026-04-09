# Deployment Cleanup Script
# Removes all development markdown and text files for production deployment

Write-Host "Starting Deployment Cleanup..." -ForegroundColor Green
Write-Host ""

# List of files to remove
$filesToRemove = @(
    "AZURE_OPENAI_MCP_SPEC_UPDATE.md",
    "BUILD_COMPLETE.md",
    "CLARIFICATION_ENGINE_GUIDE.md",
    "CLARIFICATION_ENGINE_INTEGRATION_COMPLETE.md",
    "CLARIFICATION_ENGINE_QUICK_START.md",
    "CLARIFICATION_ENGINE_TESTING_COMPLETE.md",
    "CODE_CHANGES_DETAILED.md",
    "COMPLETE_PROJECT_SUMMARY.md",
    "COMPREHENSIVE_TEST_REPORT.md",
    "CONTEXT_ISSUE_RESOLUTION.md",
    "COPILOT_REALTIME_ANSWERS_STATUS.md",
    "DEPLOYMENT_CHECKLIST.md",
    "DEPLOYMENT_GUIDE.md",
    "DEVELOPER_QUICK_START.md",
    "DOCUMENTATION_INDEX.md",
    "FEATURE_COMPLETION_REPORT.md",
    "FINAL_44_PROMPTS_TEST_REPORT.md",
    "FINAL_TEST_EXECUTION_REPORT.md",
    "FIX_COMPLETE_SUMMARY.md",
    "IMPLEMENTATION_CHECKLIST_TASK_2.md",
    "IMPROVEMENT_SUMMARY.md",
    "INTEGRATE_WITH_ASK_COPILOT.md",
    "INTEGRATION_CHECKLIST.md",
    "LOCAL_TESTING_GUIDE.md",
    "PHASE_0_BUILD_SUMMARY.md",
    "PHASE_0_DEVELOPER_GUIDE.md",
    "PHASE_0_IMPLEMENTATION_COMPLETE.md",
    "PHASE_0_INDEX.md",
    "PHASE_0_TEST_RESULTS.md",
    "PHASE_0_VERIFIED_COMPLETE.md",
    "PHASE_1_2_3_ARCHITECTURE.md",
    "PHASE_1_2_3_IMPLEMENTATION_CHECKLIST.md",
    "PHASE_1_2_3_IMPLEMENTATION_COMPLETE.md",
    "PHASE_1_2_3_QUICK_START.md",
    "PHASE_1_2_3_TEST_RESULTS.md",
    "PRODUCTION_SUMMARY.md",
    "PROJECT_COMPLETION_SUMMARY.md",
    "PROMPT_RESPONSES_CAPTURED.md",
    "QUICK_FIX_REFERENCE.md",
    "QUICK_REFERENCE.md",
    "READY_FOR_LOCAL_TESTING.md",
    "READY_FOR_UI_TESTING.md",
    "REASONING_ENGINE_IMPLEMENTATION_COMPLETE.md",
    "RUN_DEMO.md",
    "RUN_LOCAL_TESTS.md",
    "SPEC_EXECUTION_COMPLETE.md",
    "SPEC_EXECUTION_SUMMARY.md",
    "START_HERE.md",
    "TASK_2_COMPLETION_SUMMARY.md",
    "TASK_4_PHASE_0_COMPLETE.md",
    "TEST_RESULTS_FIX_SUMMARY.md",
    "TEST_RESULTS_FIXED_FINAL.md",
    "TEST_SUMMARY.txt",
    "UPDATED_TEST_RESULTS_SUMMARY.md",
    "FINAL_BUILD_SUMMARY.txt",
    "FINAL_RESOLUTION_SUMMARY.txt",
    "EXECUTION_COMPLETE.txt",
    "PHASE_0_COMPLETE.txt",
    "PHASE_0_FINAL_STATUS.txt",
    "PHASE_0_COMPLETE_SUMMARY.txt"
)

$removedCount = 0
$notFoundCount = 0

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✓ Removed: $file" -ForegroundColor Green
        $removedCount++
    } else {
        Write-Host "✗ Not found: $file" -ForegroundColor Yellow
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "Files removed: $removedCount" -ForegroundColor Green
Write-Host "Files not found: $notFoundCount" -ForegroundColor Yellow
Write-Host ""
Write-Host "Remaining files in root directory:" -ForegroundColor Cyan
Get-ChildItem -Path . -File | Where-Object { $_.Extension -in @(".md", ".txt") } | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host ""
Write-Host "Ready for Azure deployment!" -ForegroundColor Green
