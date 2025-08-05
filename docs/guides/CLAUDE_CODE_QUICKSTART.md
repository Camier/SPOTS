# 🚀 Claude Code IGN WFS Integration - Quick Start

## One-Command Integration

Run this single command to integrate IGN WFS real-time services into your SPOTS platform:

```bash
cd /home/miko/projects/spots
./run_claude_code_integration.sh
```

## What This Does

Claude Code will autonomously:

1. **📖 Read the comprehensive integration prompt** (`CLAUDE_CODE_WFS_INTEGRATION_PROMPT.md`)
2. **🔧 Integrate WFS service** into existing `src/backend/api/ign_data.py`
3. **🗺️ Update frontend map** in `src/frontend/enhanced-map-ign-advanced.html`
4. **✅ Validate integration** using the test suite
5. **🎯 Preserve all existing functionality** while adding new WFS capabilities

## Alternative Manual Command

If you prefer to run Claude Code manually:

```bash
cd /home/miko/projects/spots

claude-code \
  --file "CLAUDE_CODE_WFS_INTEGRATION_PROMPT.md" \
  --message "Integrate IGN WFS following the detailed prompt" \
  --auto-apply \
  --project-root "."
```

## After Integration

1. **Test the backend:**
```bash
cd /home/miko/projects/spots
source venv/bin/activate
uvicorn src.backend.main:app --reload

# Test new WFS endpoints
curl http://localhost:8000/api/ign/wfs/capabilities
```

2. **Test the frontend:**
```bash
python -m http.server 8085 --directory src/frontend
# Visit: http://localhost:8085/enhanced-map-ign-advanced.html
```

3. **Run validation tests:**
```bash
python test_ign_wfs_integration.py
```

## Expected Results

- ✅ 5 new WFS API endpoints working
- ✅ Interactive map analysis features  
- ✅ Real-time IGN vector data integration
- ✅ All existing functionality preserved
- ✅ 817 spots enhanced with dynamic analysis

## Files Modified

Claude Code will modify:
- `src/backend/api/ign_data.py` ← New WFS endpoints added
- `src/frontend/enhanced-map-ign-advanced.html` ← WFS client integration

## Troubleshooting

If issues occur:
1. Check the comprehensive guide: `IGN_WFS_INTEGRATION_GUIDE.md`
2. Run manual tests: `python test_ign_wfs_integration.py`
3. Verify file permissions and project structure

---

**🎯 Goal**: Transform SPOTS into a dynamic geographic analysis platform with real-time IGN data while preserving all existing excellent functionality.

**⏱️ Time**: ~1.5 hours for complete autonomous integration
