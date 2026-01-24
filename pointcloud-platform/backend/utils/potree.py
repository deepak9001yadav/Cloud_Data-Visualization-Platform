"""
============================================================================
Potree Utility Functions (Robust Version)
============================================================================
Helper functions for running PotreeConverter with:
- Detailed logging
- LAZ -> LAS fallback strategy
- Full error reporting
============================================================================
"""

import subprocess
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd: list, cwd: Path = None, timeout: int = 1800) -> Tuple[int, str, str]:
    """
    Run a subprocess command and return returncode, stdout, stderr.
    Catches exceptions and returns them as errors.
    """
    try:
        # Popen or run? process.run is safer for blocking execution
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds: {' '.join(cmd)}"
    except Exception as e:
        return -1, "", f"Execution failed: {str(e)}"

def convert_laz_to_las(input_file: Path, output_file: Path) -> Tuple[bool, str]:
    """
    Convert LAZ to LAS using PDAL translate.
    Returns: (success: bool, error_message: str)
    """
    cmd = [
        "pdal", "translate",
        str(input_file),
        str(output_file)
    ]
    
    code, out, err = run_command(cmd)
    if code != 0:
        return False, f"PDAL LAZ->LAS conversion failed.\nStdout: {out}\nStderr: {err}"
    return True, ""

def run_potree_converter(
    input_file: Path,
    output_dir: Path,
    project_name: str = "cloud",
    spacing: float = 0.0,
    levels: int = 5,
    output_format: str = "LAZ"
) -> Dict[str, Any]:
    """
    Run PotreeConverter with robust error handling and LAZ fallback.
    
    Returns a dictionary containing:
        - success: bool
        - message: str
        - command: str
        - stdout: str
        - stderr: str
        - logs: str (content of potree.log)
    """
    
    # 1. Setup paths and logging
    log_file = output_dir / "potree.log"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if PotreeConverter executable exists
    # We explicitly look in /opt/PotreeConverter/ as this preserves the 'resources' folder
    potree_bin_path = Path("/opt/PotreeConverter/PotreeConverter")
    
    if potree_bin_path.exists():
        potree_bin = str(potree_bin_path)
    else:
        # Fallback to system PATH (though this is discouraged per task specs, strictly for safety)
        potree_bin = shutil.which("PotreeConverter")
        
        if not potree_bin:
            return {
                "success": False,
                "message": "PotreeConverter executable not found",
                "command": "check /opt/PotreeConverter/PotreeConverter",
                "stdout": "",
                "stderr": f"Binary missing at {potree_bin_path} and not in PATH",
                "logs": ""
            }

    # Helper to append logs
    def write_log(content: str):
        with open(log_file, "a") as f:
            f.write(content + "\n")
            
    write_log(f"=== Starting Potree Conversion ===")
    write_log(f"Input: {input_file}")
    write_log(f"Output: {output_dir}")
    
    # 2. Build Base Command
    # Format: PotreeConverter <input> -o <output_dir> -p <project_name> --output-format <format> --overwrite
    base_cmd = [
        potree_bin,
        str(input_file),
        "-o", str(output_dir),
        "-p", project_name,
        "--output-format", output_format,
        "--overwrite"
    ]
    
    if spacing > 0:
        base_cmd.extend(["-s", str(spacing)])
    if levels > 0:
        base_cmd.extend(["-l", str(levels)])

    # 3. Execution Attempt 1 (Direct)
    write_log(f"\n--- Attempt 1: Direct Conversion ---")
    write_log(f"Command: {' '.join(base_cmd)}")
    
    code, out, err = run_command(base_cmd)
    write_log(f"Return Code: {code}")
    write_log(f"Stdout:\n{out}")
    write_log(f"Stderr:\n{err}")

    if code == 0:
        # Validation
        if validate_potree_output(output_dir, project_name):
            # Copy metadata.json to output_dir root for easier frontend access
            try:
                metadata_src = output_dir / "pointclouds" / project_name / "metadata.json"
                metadata_dst = output_dir / "metadata.json"
                shutil.copy2(metadata_src, metadata_dst)
                write_log(f"✓ Copied metadata.json to {metadata_dst}")
            except Exception as e:
                write_log(f"⚠ Warning: Could not copy metadata.json: {e}")
            
            return {
                "success": True,
                "message": "Conversion successful",
                "command": " ".join(base_cmd),
                "stdout": out,
                "stderr": err,
                "logs": log_file.read_text() if log_file.exists() else ""
            }
        else:
             write_log("\nValidation failed despite return code 0.")
    
    # 4. Fallback Strategy: LAZ -> LAS (if input is LAZ)
    is_laz = input_file.suffix.lower() == ".laz"
    
    if is_laz and code != 0:
        write_log(f"\n--- Attempt 2: Fallback (LAZ -> LAS) ---")
        write_log("Direct conversion failed. Attempting to convert LAZ to LAS first.")
        
        temp_las = input_file.with_suffix(".temp.las")
        
        # 4a. Convert to LAS
        success, laz_err = convert_laz_to_las(input_file, temp_las)
        if not success:
            write_log(f"LAZ->LAS Conversion Failed: {laz_err}")
            return {
                "success": False,
                "message": f"Fallback failed: Could not convert LAZ to LAS. {laz_err}",
                "command": "pdal translate ...",
                "stdout": out, 
                "stderr": err + "\n" + laz_err,
                "logs": log_file.read_text()
            }
            
        write_log("LAZ->LAS conversion successful. Retrying PotreeConverter with LAS file.")
        
        # 4b. Retry PotreeConverter
        fallback_cmd = [
            potree_bin,
            str(temp_las),
            "-o", str(output_dir),
            "-p", project_name,
            "--output-format", output_format,
            "--overwrite"
        ]
        
        if spacing > 0:
            fallback_cmd.extend(["-s", str(spacing)])
        if levels > 0:
            fallback_cmd.extend(["-l", str(levels)])
            
        write_log(f"Fallback Command: {' '.join(fallback_cmd)}")
        
        code_fb, out_fb, err_fb = run_command(fallback_cmd)
        
        write_log(f"Return Code: {code_fb}")
        write_log(f"Stdout:\n{out_fb}")
        write_log(f"Stderr:\n{err_fb}")
        
        # Cleanup temp file
        if temp_las.exists():
            try:
                os.remove(temp_las)
                write_log("Temporary LAS file removed.")
            except:
                write_log("Warning: Could not remove temporary LAS file.")

        if code_fb == 0:
            if validate_potree_output(output_dir, project_name):
                # Copy metadata.json to output_dir root for easier frontend access
                try:
                    metadata_src = output_dir / "pointclouds" / project_name / "metadata.json"
                    metadata_dst = output_dir / "metadata.json"
                    shutil.copy2(metadata_src, metadata_dst)
                    write_log(f"✓ Copied metadata.json to {metadata_dst}")
                except Exception as e:
                    write_log(f"⚠ Warning: Could not copy metadata.json: {e}")
                
                return {
                    "success": True,
                    "message": "Conversion successful (via fallback)",
                    "command": " ".join(fallback_cmd),
                    "stdout": out_fb,
                    "stderr": err_fb,
                    "logs": log_file.read_text()
                }
            else:
                 write_log("\nFallback validation failed.")
    
    # Final Fail State
    error_msg = "PotreeConverter failed."
    if is_laz:
        error_msg += " Both direct and fallback attempts failed."
        
    return {
        "success": False,
        "message": error_msg,
        "command": " ".join(base_cmd),
        "stdout": out, # Return original output/error
        "stderr": err,
        "logs": log_file.read_text() if log_file.exists() else "Log creation failed"
    }


def validate_potree_output(output_dir: Path, project_name: str = "cloud") -> bool:
    """
    Validate that PotreeConverter generated the expected output structure.
    
    PotreeConverter outputs to: output_dir/pointclouds/{project_name}/
    
    Valid output must have:
    - metadata.json (REQUIRED)
    - EITHER hierarchy.bin OR octree/ directory with files
    
    Note: hierarchy.bin is NOT always generated (depends on format/settings)
    """
    # The actual output directory created by PotreeConverter
    potree_output = output_dir / "pointclouds" / project_name
    
    logger.info(f"=== Validating Potree Output ===")
    logger.info(f"Checking path: {potree_output}")
    
    # 1. metadata.json is REQUIRED
    metadata_file = potree_output / "metadata.json"
    if not metadata_file.exists():
        logger.error(f"❌ REQUIRED file missing: {metadata_file}")
        return False
    logger.info(f"✓ Found metadata.json: {metadata_file}")
    
    # 2. Check for hierarchy.bin (optional)
    hierarchy_file = potree_output / "hierarchy.bin"
    has_hierarchy = hierarchy_file.exists()
    if has_hierarchy:
        logger.info(f"✓ Found hierarchy.bin: {hierarchy_file}")
    else:
        logger.info(f"ℹ hierarchy.bin not found (this is OK for some formats)")
    
    # 3. Check for octree directory (alternative to hierarchy.bin)
    octree_dir = potree_output / "octree"
    has_octree = False
    
    if octree_dir.exists() and octree_dir.is_dir():
        try:
            octree_files = list(octree_dir.iterdir())
            if octree_files:
                has_octree = True
                logger.info(f"✓ Found octree directory with {len(octree_files)} files: {octree_dir}")
            else:
                logger.warning(f"⚠ Octree directory exists but is empty: {octree_dir}")
        except Exception as e:
            logger.warning(f"⚠ Error checking octree directory: {e}")
    else:
        logger.info(f"ℹ Octree directory not found: {octree_dir}")
    
    # 4. Validation result: must have EITHER hierarchy.bin OR octree/
    if has_hierarchy or has_octree:
        logger.info("✅ Potree output validation PASSED!")
        if has_hierarchy and has_octree:
            logger.info("   → Has both hierarchy.bin AND octree/")
        elif has_hierarchy:
            logger.info("   → Has hierarchy.bin")
        else:
            logger.info("   → Has octree/ directory")
        return True
    else:
        logger.error("❌ Validation FAILED: Neither hierarchy.bin nor octree/ found")
        logger.error("   PotreeConverter output is incomplete or corrupted")
        return False


def get_potree_metadata(output_dir: Path) -> Optional[dict]:
    """Read Potree metadata.json file"""
    import json
    metadata_file = output_dir / "metadata.json"
    if not metadata_file.exists():
        return None
    try:
        with open(metadata_file, 'r') as f:
            return json.load(f)
    except:
        return None
