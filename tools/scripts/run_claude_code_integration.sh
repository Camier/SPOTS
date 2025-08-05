#!/bin/bash
# Claude Code Integration Command for IGN WFS

cd /home/miko/projects/spots

# Run Claude Code with the comprehensive integration prompt
claude-code \
  --file "CLAUDE_CODE_WFS_INTEGRATION_PROMPT.md" \
  --message "Integrate the IGN WFS real-time vector services into the existing SPOTS platform following the detailed prompt. Preserve all existing functionality while adding the new WFS capabilities. Focus on backend integration first (ign_data.py), then frontend (enhanced-map-ign-advanced.html), then validation testing." \
  --auto-apply \
  --include-context \
  --project-root "." \
  --max-iterations 3

echo "🎯 Claude Code WFS Integration Started!"
echo "📂 Working directory: $(pwd)"
echo "📋 Integration prompt: CLAUDE_CODE_WFS_INTEGRATION_PROMPT.md"
echo ""
echo "Expected changes:"
echo "  ✅ Backend: WFS endpoints added to src/backend/api/ign_data.py"
echo "  ✅ Frontend: WFS client integrated into enhanced-map-ign-advanced.html"  
echo "  ✅ Testing: Validation with test_ign_wfs_integration.py"
echo ""
echo "⏱️  Estimated completion: 1.5 hours"
