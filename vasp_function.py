from pymatgen.core import Lattice, Structure
from pymatgen.io.vasp import Poscar
import subprocess
import re
import os

def generate_vasp_config(calcdir):
    """
    调用外部脚本生成 VASP 额外的配置文件。
    
    这里使用 subprocess.run() 调用 Python 脚本 "VASPTemplates/vt.py"，
    并传入参数 "test.vt"，外部脚本会根据这个文件生成相应的 VASP 输入配置。
    """
    subprocess.run(["python", "VASPTemplates/vt.py", "test.vt", calcdir])

def write_vasp_config(vt_config: str, calcdir: str):
    """
    从生成的实验配置中提取VASP配置文件，确保其准确性和可行性，生成VASP配置文件。
    
    输入格式要求为：

    ---XX.VT---
    [xx.vt 文件的配置内容]
    
    calcdir: 计算目录路径，取文件夹名
    
    参数:
      vt_config: 生成的vt实验配置，其中包含 xx.vt 文件的配置内容。

    输出:
        VASP 输入文件
    """
    
    # 使用正则表达式提取 vt_config 部分，即 "---XX.VT---" 后面的所有文本
    vt_pattern = r"---XX\.VT---\s*(.*)"
    vt_match = re.search(vt_pattern, vt_config, re.DOTALL)
    if vt_match:
        vt_content = vt_match.group(1).strip()
    else:
        raise ValueError("在 LLM 输出中未找到 xx.vt 配置内容。")
    
    lines = vt_content.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    vt_config = "\n".join(cleaned_lines)
    
    # 将整理好的 vt_config 写入 "test.vt" 文件
    with open("test.vt", "w") as f:
        f.write(vt_config)
    
    generate_vasp_config(calcdir)
    os.remove("test.vt")
    os.remove("POSCAR")
    return f"VASP输入文件已生成,实验验证成功，calcdir是{calcdir}"

from PyPDF2 import PdfReader
import time
def read_vasp_pdf(pdf_path:str):
    """
    读取VASP的PDF文件
    输入：pdf_path，PDF文件路径
    输出：PDF文件的文本内容
    """
    pdf_text = str()
    reader = PdfReader(pdf_path)
    for page_number, page in enumerate(reader.pages, start=1):
        # Extract text from the page
        try:
            text = page.extract_text()
        except Exception as e:
            return "EXTRACTION FAILED"

        # Do something with the text (e.g., print it)
        pdf_text += f"--- Page {page_number} ---"
        pdf_text += text
        pdf_text += "\n"
    return pdf_text


import xml.etree.ElementTree as ET

class VasprunParser:
    def __init__(self, path):
        self.path = path

    def get_root(self):
        tree = ET.parse(self.path)
        return tree.getroot()

    def generator(self):
        gen_node = list(self.get_root())[0]
        return [(item.attrib['name'], item.text) for item in gen_node.iter('i')]

    def incar(self):
        inc_node = list(self.get_root())[1]
        return [(item.attrib['name'], item.text) for item in inc_node.iter('i')]

    def monkhorst_pack(self):
        kpoints = list(self.get_root())[2]
        first_block = list(kpoints)[0]
        return [(item.attrib['name'], item.text.split()) for item in list(first_block)]

    def kpoints_list(self):
        kpoints = list(self.get_root())[2]
        coord_block = list(kpoints)[1]
        return [v.text.split() for v in coord_block.findall('v')]

    def kpoints_weight(self):
        kpoints = list(self.get_root())[2]
        children = list(kpoints)
        if len(children) >= 3:
            weight_block = children[2]
            return [v.text.strip() for v in weight_block.findall('v')]
        else:
            return []  # 或者 return ['1.0']*len(self.kpoints_list()) 默认均匀权重

    def parameters(self):
        param = list(self.get_root())[3]
        result = []

        for item in param.iter('i'):
            result.append((item.attrib.get('name'), item.text.strip()))

        for item in param.iter('v'):
            name = item.attrib.get('name')  # 安全访问
            if name is not None:
                result.append((name, item.text.split()))
            else:
                # 你可以选择跳过或加个标记，例如：
                result.append(("unnamed_v", item.text.split()))
        
        return result

    def atoms_info(self):
        atinfo = list(self.get_root())[4]
        children = list(atinfo)
        info = [
            ('No. of atoms', children[0].text.strip()),
            ('atom types', children[1].text.strip())
        ]
        for c in atinfo.iter('c'):
            info.append(c.text.strip())
        return info

    def structure(self):
        cstruct = []
        atom_struct = list(self.get_root())[5]
        crystal = atom_struct.find('crystal')

        if crystal is not None:
            elem_varrays = crystal.findall('varray')
            elemi = crystal.find('i')

            for varray in elem_varrays:
                vectors = [v.text.split() for v in varray.findall('v')]
                cstruct.append((varray.attrib['name'], vectors))

            if elemi is not None:
                cstruct.append((elemi.attrib['name'], elemi.text.strip()))
        else:
            cstruct.append(("crystal", "Not found"))

        for varray in atom_struct.findall('varray'):
            vectors = [v.text.split() for v in varray.findall('v')]
            cstruct.append((varray.attrib['name'], vectors))

        return cstruct

    def calculation(self):
        calc_res = []
        calc_forces = []
        calc_positions = []

        all_steps = list(self.get_root())[6:]  # skip first 6 blocks (header info)

        for step in all_steps:
            tag_list = []
            cpos = []
            cforces = []

            for itag in step.iter('i'):
                tag_list.append((itag.attrib['name'], itag.text.strip()))
            for timetag in step.iter('time'):
                tag_list.append((timetag.attrib['name'], timetag.text.split()))

            structure = step.find('structure')
            if structure is not None:
                varrays = structure.findall('varray')
                if varrays:
                    for v in varrays[0].iter('v'):
                        cpos.append(v.text.split())

            force_varray = step.findall('varray')
            if force_varray:
                for v in force_varray[0].iter('v'):
                    cforces.append(v.text.split())

            calc_res.append(tag_list)
            calc_positions.append(cpos)
            calc_forces.append(cforces)

        return calc_res, calc_positions, calc_forces
    


def analyze_vasprun_all(xml_path: str):
    """
    分析VASP计算结果，用于完成实验报告
    输入：xml_path，VASP计算结果路径
    输出：VASP计算结果分析
    """
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
                "properties": r[:3],  # limit for brevity
                "first_2_positions": p[:2],
                "first_2_forces": f[:2]
            })
        result["calculation_steps"] = calc_summary
    except Exception as e:
        result["calculation_steps"] = f"Failed to parse calculation steps: {e}"

    return result


def write_vasp_report(xml_result: str):
    """
    将计算报告的具体内容写入报告文件
    输入：计算报告的具体内容
    输出：将计算报告写入experiment_report.txt
    """
    with open("experiment_report.txt", "w") as f:
        f.write(xml_result)
    return "报告已写入experiment_report.txt"




import json
import re
import warnings
import requests
import time
import os
from pymatgen.core import Lattice, Structure, Element
from pymatgen.io.vasp.inputs import Poscar
import openai


class SimPleChat:
    def __init__(self, system="你是一个在晶体结构领域的专家"):
        self.system = system
        self.refresh()

        key_dict = dict(
            DEEP_SEEK_BASE_URL="https://api.deepseek.com",
            DEEP_SEEK_API_KEY=os.getenv("DEEP_SEEK_API_KEY"),
        )
        assert key_dict["DEEP_SEEK_API_KEY"], "Please set the DEEP_SEEK_API_KEY."
        self.client = openai.OpenAI(
            api_key=key_dict["DEEP_SEEK_API_KEY"],
            base_url=key_dict["DEEP_SEEK_BASE_URL"],
        )
        self.model = key_dict.get("OPENAI_MODEL_NAME", "deepseek-chat")

    def refresh(self):
        self.messages = [{"role": "system", "content": self.system}]

    def _ask(self, msg):
        chat_completion = self.client.chat.completions.create(
            model=self.model, messages=msg, response_format={"type": "text"}
        )
        return chat_completion.choices[0].message.content

    def Q(self, question):
        self.messages.append({"role": "user", "content": str(question)})
        answer = self._ask(self.messages)
        self.messages.append({"role": "assistant", "content": str(answer)})
        return answer


def rep_string(string: str) -> str:
    if "```json" in string:
        match = re.search(r"```json(.*?)```", string, re.DOTALL)
        if not match:
            raise ValueError("No JSON block found.")
        string = match.group(1).replace("\n", "")
    else:
        string = string.replace("\n", "").replace("'", '"')
    return string


def download_mp(material_id: str) -> Structure:
    from pymatgen.ext.matproj import MPRester

    os.environ["HTTP_PROXY"] = "http://114.115.170.192:8118"
    os.environ["HTTPS_PROXY"] = "http://114.115.170.192:8118"
    API_KEY = "msZce01AjFltxEu97whgD2TBdQYwdxhQ"
    with MPRester(API_KEY) as mpr:
        structure = mpr.get_structure_by_material_id(material_id)
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    return structure


def get_structure_dp_database(formula: str, space_group: int | None = None, *, max_retries: int = 5):
    url = "https://materials-db-agent.mlops.dp.tech/query/openai"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    text = (
        f"请给出空间群号为 {space_group} ,化学式为 {formula} ,的晶体结构。"
        if space_group
        else f"请给出化学式为 {formula} 的晶体结构。"
    )
    payload = {"text": text, "limit": 3}

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    break
            data = []
        except Exception:
            data = []

        if attempt < max_retries:
            time.sleep(1)
        else:
            data = []

    if not data:
        return []

    res_data = []
    for item in data:
        res = {
            "formula": item.get("formula", ""),
            "material_id": item.get("material_id", ""),
        }
        res["structure"] = download_mp(res["material_id"])
        res_data.append(res)
    return res_data


def _search_poscar_template_once(formula: str):
    ba = SimPleChat(system="你是一个在晶体结构领域的专家")

    ba.Q(
        "1. 根据下文给出的元素种类及配比,判断是否多类元素通过原子置换的方式占据了同类位点,给出同类位点的元素分组信息。"
        "如果化学式中,判断部分为掺杂或吸附元素(如H,OH,轻金属等),而不是基础结构本身元素,分别在base、adsorb分别给出基础结构和掺杂/吸附的元素配比信息。"
    )
    ba.Q(f"需要分析的化学式为 {formula}")
    res = ba.Q(
        """
        将上述结果,按照各位点(A,B,C,...)配比的公约数尝试简化为最简整数配比,并分别将同位置的元素类别分别带入位点,获得多个不同的化学式及公约数。
        返回所有可能的化学式(包含减去吸附原子的base化学式)的字典及公约数, 如下：

        {
        "base":{"A":{"Sr":3,"Ca":1,"all":4},"B":{"Ti":4,"all":4},"C":{"O":12,"all":12}},
        "adsorb":{},
        "temps":{"Sr3CaTi4O12":1,"SrTiO3":4,"CaTiO3":4}
        }

        注意：只返回结果字典,不要任何其他解释性信息。
        """
    )
    res = json.loads(rep_string(res))

    base = res.get("base", {})
    temps = res.get("temps", {})
    adsorb = res.get("adsorb", {})

    msgs = []
    sup = {
        1: (1, 1, 1),
        2: (2, 1, 1),
        3: (3, 1, 1),
        4: (2, 2, 1),
        5: (5, 1, 1),
        6: (2, 3, 1),
        7: (7, 1, 1),
        8: (2, 2, 2),
        9: (3, 3, 1),
        10: (5, 2, 1),
        11: (11, 1, 1),
        12: (3, 2, 2),
    }

    for cur_formula, factor in temps.items():
        factor = int(factor)
        msg = get_structure_dp_database(cur_formula)
        if not msg:
            continue

        for mi in msg:
            structure = mi["structure"].copy()
            structure.make_supercell(sup.get(factor, (1, 1, 1)))
            mi["space_group"] = structure.get_space_group_info()

            if factor != 1 and base:
                for bv in base.values():
                    bv.pop("all", None)
                    names = [elm for elm, num in bv.items() for _ in range(int(num))]
                    idxs = [i for i, s in enumerate(structure.symbol_set) if s in names]
                    if len(idxs) == len(names):
                        for idx, new_sym in zip(idxs, names):
                            structure.replace(idx, new_sym)

            if adsorb:
                prompt_ads = (
                    f"吸附/掺杂元素种类及个数信息为：{adsorb}"
                    f"。请根据已有基底结构{structure}, 估计合理的分数坐标。"
                    "注意：只返回结果字典,不要任何其他解释性信息。"
                )
                res_ads = json.loads(rep_string(ba.Q(prompt_ads)))
                for sym, coords in res_ads.items():
                    structure.append(sym, coords)

            mi.update(
                {
                    "structure": structure,
                    "adsorb": adsorb,
                    "base": base,
                    "species": structure.symbol_set,
                    "abc": structure.lattice.abc,
                    "angle": structure.lattice.angles,
                    "fractional_coords": structure.frac_coords.tolist(),
                    "reference_formula": mi.pop("formula", cur_formula),
                    "reference_material_id": mi.pop("material_id", ""),
                    "poscar": Poscar(structure),
                }
            )
            mi["poscar_str"] = str(mi["poscar"])
            msgs.append(mi)

    if not msgs:
        raise ValueError("未能获取合适的结构模板。")

    with open(
        "/bohr/paperagent-vgwq/v4/science-agent-framework/prompt/format.txt", "r"
    ) as fp:
        vt_format = fp.read()

    return {"poscar_template": msgs[0]["poscar_str"], "vt_format": vt_format}


def search_poscar_template(formula: str, *, max_retries: int = 5):
    """
    尝试整个流程最多 max_retries 次，直到成功返回。
    """
    for attempt in range(1, max_retries + 1):
        try:
            return _search_poscar_template_once(formula)
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(1)



def write_poscar(final_poscar: str):
    """
    用于从模板中搜索，并进行原子替换，返回满足要求的用于VASP计算的POSCAR文件内容
    输入：POSCAR文件内容
    输出：POSCAR文件内容
    """
    structure = Poscar.from_str(str(final_poscar)).structure
    Poscar(structure).write_file("POSCAR")
    return final_poscar


def check_vasp_input(calcdir: str):
    """
    用于检查VASP输入文件是否存在
    输入：calcdir，计算目录路径
    输出：文件是否存在
    """
    if os.path.exists(calcdir):
        return "🎉所有配置文件均已生成"
    else:
        if os.path.exists("POSCAR"):
            return "🚫POSCAR文件不存在"
        if os.path.exists(os.path.join(calcdir, "XX.VT")):
            return "🚫XX.VT文件不存在"
        return "🚫所有配置文件均不存在"

