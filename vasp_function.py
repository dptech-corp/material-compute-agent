from pymatgen.core import Structure
from pymatgen.io.vasp import Poscar
import subprocess
import re
import os
import json
import re
import warnings
import requests
from pymatgen.core import Lattice, Structure,Element
from pymatgen.io.vasp.inputs import Poscar
import openai
from PyPDF2 import PdfReader
from utils import *


def generate_vasp_config(calcdir: str):
    """
    Generate VASP input configuration files using an external script.

    This function calls the external Python script "VASPTemplates/vt.py"
    with the input file "test.vt" and the calculation directory `calcdir`.

    Args:
        calcdir (str): Path to the calculation directory where VASP inputs will be created.

    Example:
        generate_vasp_config("tmp/my_calc")
    """
    subprocess.run(["python", "VASPTemplates/vt.py", "test.vt", calcdir])


def write_vasp_config(vt_config: str, calcdir: str) -> str:
    """
    Extract and write VASP input configuration from a structured vt_config string.

    This function parses the config content after the '---XX.VT---' tag,
    writes it to "test.vt", and uses the external script to generate
    VASP input files in a temporary subdirectory.

    Args:
        vt_config (str): Configuration content that includes a section marked with '---XX.VT---'.
        calcdir (str): Name of the folder where the VASP input files will be written.

    Returns:
        str: Success message with the absolute path of the generated calculation directory.

    Raises:
        ValueError: If no configuration content is found under the '---XX.VT---' tag.

    Example:
        vt_data = '''
        Some description...
        ---XX.VT---
        SYSTEM = Test
        ENCUT = 520
        '''
        write_vasp_config(vt_data, "my_calc")
    """

    # Extract configuration content under the '---XX.VT---' section
    vt_pattern = r"---XX\.VT---\s*(.*)"
    vt_match = re.search(vt_pattern, vt_config, re.DOTALL)

    if vt_match:
        vt_content = vt_match.group(1).strip()
    else:
        raise ValueError("Failed to find xx.vt configuration content in the provided string.")

    # Clean and write configuration lines to "test.vt"
    lines = vt_content.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    vt_config_cleaned = "\n".join(cleaned_lines)

    with open("test.vt", "w") as f:
        f.write(vt_config_cleaned)

    # Prepare temporary calculation directory
    os.makedirs("tmp", exist_ok=True)
    calcdir_path = os.path.join("tmp", calcdir)

    # Generate VASP input files
    generate_vasp_config(calcdir_path)

    # Clean up intermediate file

    return f"VASP input files generated successfully. calcdir: {calcdir_path}"


def read_vasp_pdf(pdf_path: str) -> str:
    """
    Read and extract text from a VASP-generated PDF file.

    This function reads a PDF file located at `pdf_path` and extracts text
    content from each page, concatenating the results into a single string.
    If any page fails to be extracted, it returns "EXTRACTION FAILED".

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF, or "EXTRACTION FAILED" if an error occurs.

    Example:
        pdf_content = read_vasp_pdf("vasp_output.pdf")
        print(pdf_content)
    """
    pdf_text = ""

    reader = PdfReader(pdf_path)

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
        except Exception as e:
            return "EXTRACTION FAILED"

        pdf_text += f"--- Page {page_number} ---\n"
        pdf_text += text if text else ""
        pdf_text += "\n"

    return pdf_text


def analyze_vasprun_all() -> list:
    """
    Analyze all VASP calculation results in the server/tmp directory.

    For each subdirectory under "server/tmp", the function attempts to locate a
    "vasprun.xml" file and parse various pieces of information using VasprunParser.

    Returns:
        list: A list of dictionaries, each representing parsed results from one VASP run.

    Example:
        results = analyze_vasprun_all()
        for res in results:
            print(res["generator"])
    """
    out_path = "server/tmp"
    experiment_path = os.listdir(out_path)
    result_list = []

    for path in experiment_path:
        path = os.path.join(out_path, path)
        xml_path = os.path.join(path, "vasprun.xml")

        parser = VasprunParser(xml_path)
        result = {}

        try:
            result["generator"] = parser.generator()
        except Exception as e:
            result["generator"] = f"Failed to parse generator info: {e}"

        try:
            result["incar"] = parser.incar()
        except Exception as e:
            result["incar"] = f"Failed to parse INCAR: {e}"

        try:
            result["kpoints_grid"] = parser.monkhorst_pack()
        except Exception as e:
            result["kpoints_grid"] = f"Failed to parse K-points grid: {e}"

        try:
            result["kpoints_list"] = parser.kpoints_list()
        except Exception as e:
            result["kpoints_list"] = f"Failed to parse K-points list: {e}"

        try:
            weights = parser.kpoints_weight()
            result["kpoints_weight"] = weights if weights else "No weight info (likely Gamma or auto K-points)"
        except Exception as e:
            result["kpoints_weight"] = f"Failed to parse K-points weight: {e}"

        try:
            result["parameters"] = parser.parameters()
        except Exception as e:
            result["parameters"] = f"Failed to parse parameters: {e}"

        try:
            result["atoms_info"] = parser.atoms_info()
        except Exception as e:
            result["atoms_info"] = f"Failed to parse atom info: {e}"

        try:
            result["structure"] = parser.structure()
        except Exception as e:
            result["structure"] = f"Failed to parse structure: {e}"

        try:
            calc_res, calc_pos, calc_forces = parser.calculation()
            calc_summary = []
            for step_id, (r, p, f) in enumerate(zip(calc_res, calc_pos, calc_forces)):
                calc_summary.append({
                    "step": step_id,
                    "properties": r[:3],            # Show only first 3 properties
                    "first_2_positions": p[:2],     # Show only first 2 atoms
                    "first_2_forces": f[:2]         # Show only first 2 force vectors
                })
            result["calculation_steps"] = calc_summary
        except Exception as e:
            result["calculation_steps"] = f"Failed to parse calculation steps: {e}"

        result_list.append(result)

    return result_list


def write_vasp_report(xml_result: str) -> str:
    """
    Write the analysis results into a report file named "experiment_report.txt".

    Args:
        xml_result (str): The textual content of the VASP analysis report.

    Returns:
        str: A confirmation message after writing the report.

    Example:
        write_vasp_report("VASP Report Content Here")
    """
    with open("experiment_report.txt", "w") as f:
        f.write(xml_result)

    return "Report written to experiment_report.txt"

def search_poscar_template(formula: str) -> str:
    """
    Search for a POSCAR template based on the given chemical formula.

    This function retrieves a structural template file (POSCAR format) for a given 
    compound formula, such as "Sr5Ca3Fe8O24". The returned template is intended 
    to be manually adjusted by a researcher (e.g., a PhD student) to ensure that 
    all atom types, counts, and positions strictly match the specified formula.

    Args:
        formula (str): The chemical formula, e.g., "Sr5Ca3Fe8O24".

    Returns:
        str: The content of a POSCAR template file.

    Example:
        template = search_poscar_template("Sr5Ca3Fe8O24")
    """
    return search_poscar_template_tool(formula)
    

def write_poscar(final_poscar: str) -> str:
    """
    Write a final POSCAR content string to a file named 'POSCAR'.

    This function parses the given POSCAR string to create a structure object 
    using Pymatgen, then writes it into a file named "POSCAR" in the current directory.

    Args:
        final_poscar (str): The full content of a POSCAR file (e.g., after atomic substitution).

    Returns:
        str: The original POSCAR content.

    Example:
        poscar_str = "...POSCAR content..."
        write_poscar(poscar_str)
    """
    try:
        structure = Poscar.from_str(str(final_poscar)).structure
        Poscar(structure).write_file("POSCAR")
        return final_poscar
    except Exception as e:
        return f"Failed to write POSCAR: {e}"

def show_vasp_config(calcdir: str) -> dict:
    """
    Display key VASP input configuration files to the user (currently only INCAR).

    This function attempts to read the content of 'INCAR' in the specified 
    calculation directory. If the directory or file is not found, an error message 
    will be returned.

    Args:
        calcdir (str): Full path or subpath under 'tmp/' where VASP input files are stored.

    Returns:
        dict: A dictionary containing the content of the 'INCAR' file, or an error message.

    Example:
        config_info = show_vasp_config("tmp/my_calc")
        print(config_info["INCAR"])

    Raises:
        FileNotFoundError: If the specified directory or 'INCAR' file does not exist.
    """
    if not os.path.exists(calcdir):
        calcdir = os.path.join("tmp", calcdir)
        if not os.path.exists(calcdir):
            return {"error": "Calculation directory does not exist."}

    result = {}
    for config in ["INCAR"]:
        config_path = os.path.join(calcdir, config)
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                result[config] = f.read()
        else:
            result[config] = f"Error: {config} file not found."

    return result


def check_vasp_input(calcdir: str) -> dict:
    """
    Check if the VASP input directory exists.

    This function verifies the existence of the specified calculation directory.
    If the directory is not found, it will also try the "tmp/" subdirectory.

    Args:
        calcdir (str): Path to the VASP calculation directory.

    Returns:
        dict: A dictionary with either a success message or an error message.

    Example:
        result = check_vasp_input("my_calc")
        if result.get("success"):
            print(result["message"])
    """
    if not os.path.exists(calcdir):
        calcdir = os.path.join("tmp", calcdir)
        if not os.path.exists(calcdir):
            return {"error": "Calculation directory does not exist."}
        
    os.remove("test.vt")
    os.remove("POSCAR")
    return {"success": True, "message": f"Calculation directory found at: {calcdir}"}


def rewrite_vasp_config(calcdir: str, config: str, new_content: str) -> dict:
    """
    Rewrite a VASP input configuration file (e.g., INCAR or POSCAR) with new content.

    This function updates the content of a given VASP config file located in the specified directory.
    It first checks whether the directory and target file exist, and if so, writes the new content to it.

    Args:
        calcdir (str): Path to the calculation directory containing VASP input files.
        config (str): The name of the config file to rewrite (e.g., "INCAR", "POSCAR").
        new_content (str): The new content to write into the file.

    Returns:
        dict: A dictionary indicating the result of the operation (success or error).

    Example:
        new_incar = "ENCUT = 520\nISMEAR = 0"
        result = rewrite_vasp_config("tmp/my_calc", "INCAR", new_incar)
        print(result["message"]) if result.get("success") else print(result["error"])
    """
    if not os.path.exists(calcdir):
        calcdir = os.path.join("tmp", calcdir)
        if not os.path.exists(calcdir):
            return {"error": "Calculation directory does not exist."}

    config_path = os.path.join(calcdir, config)
    
    if not os.path.exists(config_path):
        return {"error": f"Error: {config} file does not exist."}
    
    try:
        with open(config_path, "w") as f:
            f.write(new_content)
        return {
            "success": True,
            "message": f"{config} file successfully rewritten.",
            "new_content": new_content
        }
    except Exception as e:
        return {"error": f"Failed to rewrite {config}: {str(e)}"}