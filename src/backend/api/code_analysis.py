#!/usr/bin/env python3
"""API endpoints for code analysis and improvement"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional, Dict
import logging
from pathlib import Path
import tempfile
import shutil

from ..services.code_improvement_service import CodeImprovementService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize code improvement service
code_service = CodeImprovementService()


@router.post("/analyze-code")
async def analyze_code(file: UploadFile = File(...)):
    """
    Analyze uploaded code file for improvements

    Returns comprehensive analysis including:
    - Code quality metrics
    - Security vulnerabilities
    - Style issues
    - AI-powered suggestions
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Analyze the code
        analysis = code_service.analyze_code_file(tmp_path)

        # Clean up
        Path(tmp_path).unlink()

        return {"filename": file.filename, "analysis": analysis, "status": "success"}

    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-project-file")
async def analyze_project_file(file_path: str):
    """
    Analyze a file from the SPOTS project

    Provide relative path from project root
    """
    try:
        # Build full path
        project_root = Path(__file__).parent.parent.parent.parent
        full_path = project_root / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path must be a file")

        # Analyze the code
        analysis = code_service.analyze_code_file(str(full_path))

        return {"file_path": file_path, "analysis": analysis, "status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project file analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code-health-report")
async def get_code_health_report():
    """
    Generate a health report for key SPOTS modules
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent

        # Key files to analyze
        key_files = [
            "src/backend/services/ign_wfs_service.py",
            "src/frontend/js/ign-wfs-client.js",
            "src/backend/api/ign_data.py",
            "src/backend/main.py",
        ]

        report = {
            "overall_health": "good",
            "files_analyzed": 0,
            "total_issues": 0,
            "security_vulnerabilities": 0,
            "modules": [],
        }

        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                analysis = code_service.analyze_code_file(str(full_path))

                module_report = {
                    "file": file_path,
                    "language": analysis.get("language", "unknown"),
                    "lines": analysis.get("lines", 0),
                    "issues_count": len(analysis.get("issues", [])),
                    "security_risk": analysis.get("security", {}).get("risk_level", "low"),
                    "documentation_coverage": analysis.get("documentation", {}).get("comment_density", 0),
                }

                # Count issues
                if "issues" in analysis:
                    report["total_issues"] += len(analysis["issues"])

                if "security" in analysis:
                    report["security_vulnerabilities"] += len(analysis["security"].get("vulnerabilities", []))

                report["modules"].append(module_report)
                report["files_analyzed"] += 1

        # Calculate overall health
        if report["security_vulnerabilities"] > 0:
            report["overall_health"] = "needs_attention"
        elif report["total_issues"] > 10:
            report["overall_health"] = "fair"

        return report

    except Exception as e:
        logger.error(f"Health report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from pydantic import BaseModel


class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    context: Optional[str] = None


@router.post("/suggest-improvements")
async def suggest_improvements(request: CodeAnalysisRequest):
    """
    Get AI-powered code improvement suggestions

    Provide code snippet and language
    """
    try:
        # Get AI suggestions
        suggestions = code_service._get_ai_suggestions(request.code, request.language)

        # Get refactoring suggestions
        refactorings = code_service.suggest_refactoring(request.code, request.language)

        # Security analysis
        security = code_service._analyze_security(request.code, request.language)

        return {
            "ai_suggestions": suggestions,
            "refactoring_opportunities": refactorings,
            "security_analysis": security,
            "language": request.language,
            "context": request.context,
        }

    except Exception as e:
        logger.error(f"Suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code-metrics/{module}")
async def get_code_metrics(module: str):
    """
    Get detailed metrics for a specific module

    Modules: backend, frontend, tests
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent

        module_paths = {"backend": "src/backend", "frontend": "src/frontend", "tests": "src/backend/tests"}

        if module not in module_paths:
            raise HTTPException(status_code=400, detail=f"Invalid module: {module}")

        module_path = project_root / module_paths[module]

        metrics = {
            "module": module,
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
            "complexity": {"average": 0, "max": 0},
            "documentation": {"documented_functions": 0, "total_functions": 0},
        }

        # Analyze all Python/JS files in module
        for file_path in module_path.rglob("*.py"):
            metrics["total_files"] += 1
            analysis = code_service.analyze_code_file(str(file_path))

            if "lines" in analysis:
                metrics["total_lines"] += analysis["lines"]

            # Update language stats
            lang = analysis.get("language", "unknown")
            metrics["languages"][lang] = metrics["languages"].get(lang, 0) + 1

            # Update documentation stats
            if "documentation" in analysis:
                doc = analysis["documentation"]
                metrics["documentation"]["documented_functions"] += doc.get("function_docs", 0)
                metrics["documentation"]["total_functions"] += doc.get("total_functions", 0)

        # Calculate documentation percentage
        if metrics["documentation"]["total_functions"] > 0:
            metrics["documentation"]["coverage_percent"] = (
                metrics["documentation"]["documented_functions"] / metrics["documentation"]["total_functions"] * 100
            )
        else:
            metrics["documentation"]["coverage_percent"] = 0

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
