from pymatgen.core import Lattice, Structure
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

from pymatgen.io.cif import CifParser
import openai

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




class SimPleChat:
    def __init__(self,
                 system: str = "你是一个在晶体结构领域的专家",
                 deployment_name: str = None):
        # 系统提示
        self.system = system

        api_key = os.environ.get("AZURE_OPENAI_API_KEY") 
        openai.api_key = api_key
        openai.api_type = "azure"
        openai.api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
        openai.api_version = os.environ.get("AZURE_API_VERSION")
        assert openai.api_base, "Please set AZURE_OPENAI_BASE_URL in environment."
        assert openai.api_version, "Please set AZURE_API_VERSION in environment."

        self.deployment_name = deployment_name or os.environ.get("AZURE_DEPLOYMENT_NAME")
        assert self.deployment_name, "Please set AZURE_DEPLOYMENT_NAME in environment."

        self.refresh()

    def refresh(self):
        self.messages = [{"role": "system", "content": self.system}]

    def _ask(self, user_prompt: str) -> str:
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_prompt})
        resp = openai.ChatCompletion.create(
            engine=self.deployment_name,
            messages=self.messages,
            temperature=0.1,
            max_tokens=2048,
        )
        answer = resp.choices[0].message.content
        self.messages.append({"role": "assistant", "content": answer})
        return answer


    def Q(self,question):
        self.messages.append({"role": "user", "content": str(question)})
        answer = self._ask(self.messages)
        self.messages.append({"role": "assistant", "content": str(answer)})
        return answer
    
    

def make_float(strs):
    if "/" in strs:
        strs = strs.split("/")
        return float(strs[0])/float(strs[1])
    else:
        return float(strs)
    
def map_local_cif(material_id):
    mp_root_dir = os.getenv("MP_ROOT_DIR")

    exact_name = f"{material_id}.cif"
    exact_path = os.path.join(mp_root_dir, exact_name)
    if os.path.isfile(exact_path):
        return Structure.from_file(exact_path)
    else:
        raise FileNotFoundError(f"File {exact_path} not found.")


def get_structure_mp_database(formula,space_group=None):
    from pymatgen.ext.matproj import MPRester
    API_KEY = "msZce01AjFltxEu97whgD2TBdQYwdxhQ"

    # 下载结构并保存为 POSCAR 和 CIF 文件
    with MPRester(API_KEY) as mpr:
        results = mpr.get_entries(formula, sort_by_e_above_hull=True)

    res_data = []
    for n,entry in enumerate(results):
        res = {}
        
        entry_id = entry.entry_id  # e.g., "mp-22474"

        # 获取结构信息
        structure = entry.structure
        
        res["formula"] =  entry.composition.formula
        res["material_id"] =  entry.data.get("material_id","")
        res["entry_id"] =  entry_id
        res["structure"] = structure
        
        if space_group:
            sg,sgn = structure.get_space_group_info()
            if isinstance(space_group, str) and space_group == sg:
                res_data.append(res)
            elif isinstance(space_group, int) and space_group == sgn:
                res_data.append(res)
        else:
            res_data.append(res)
                
        if len(res_data) >= 3:
            break
        
    return res_data
    

def get_structure_dp_database(formula,space_group=None):
    
    url = "https://materials-db-agent.mlops.dp.tech/query/openai"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    if space_group:
        text = f"请给出空间群号为 {space_group} ,化学式为 {formula} ,的晶体结构。"
    else:
        text = f"请给出化学式为 {formula} 的晶体结构。"
    
    payload = {
        "text": text,  # Replace with your actual query text
        "limit": 3        # You can adjust the limit as needed
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()  # Get the JSON response data
        # print("Response data:", data)
    else:
        # print(f"Request failed with status code {response.status_code}")
        # print("Response:", response.text)
        raise Exception(f"Request failed with status code {response.status_code}")
    
    data = data.get("data", [])
    if not data:
        return []
    
    res_data = []
    for item in data:
        res = {}
        res["formula"] =  item.get('formula',"")
        res["material_id"] =  item.get('material_id',"")
        
        # method 1
        structure =  map_local_cif(item.get('material_id'))
        
        res["structure"] = structure
        res_data.append(res)


    return res_data

def rep_string(string):
    if "```json" in string:
        json_pattern = r"```json(.*?)```"
        match = re.search(json_pattern, string, re.DOTALL)
        if match:
            code = match.group(1)
        else:
            raise ValueError("No JSON block found in the string.")
        string = re.sub(json_pattern, r"\1", code).replace("\n", "")
    else:
        string = string.replace("\n", "")
        string = string.replace("'", '"')
    return string


def check_structure(structure,space_group=None):
    # score = []
    if space_group:
        sg,sgn = structure.get_space_group_info()
        if isinstance(space_group, str) and space_group == sg:
            return True
        elif isinstance(space_group, int) and space_group == sgn:
            return True
        else:
            return False
    else:
        return True
    
    
def search_poscar_template(formula: str):
    """
    对化学式进行数据库匹配、超胞扩展、原子替换和吸附处理后返回POSCAR模板

    输入：化学式，比如"Sr5Ca3Fe8O24"
    输出：POSCAR模板文件内容，这里只是模板，需要博士生根据模板进行原子替换，确保结构中的所有原子种类、数量和分布都严格符合输入化学式。
    

    """
    # 1. 获得解析后的文献,问询大模型
    ba = SimPleChat(system="你是一个在晶体结构领域的专家")

    prompt1 = """1. 根据下文给出的元素种类及配比,判断是否多类元素通过原子置换的方式占据了同类位点,给出同类位点的元素分组信息。
    如果化学式中,判断部分为掺杂或吸附元素(如H,OH,轻金属等),而不是基础结构本身元素,分别在base、adsorb分别给出基础结构和掺杂/吸附的元素配比信息。adsorb元素不需要进行分组。
    例如 "Sr3CaTi4O12"中, 假定Sr与Ca占据同类位点,Sr3CaTi4O12的那么化学式模板为A4B4O12,根据公约数,可简化为 ABO3 形式,而该形式正好符合钙钛矿ABO3模板。
    因此 根据晶体学经验,"Sr3CaTi4O12" 的分组信息如下：
    {
    "base":{
        "A":{"Sr":3,"Ca":1,"all":4},
        "B":{"Ti":4,"all":4},
        "C":{"O":12,"all":12},
    },
    "adsorb":{}
    }
    注意,上述分析应当首先检测是否已经符合已知材料种类配比,例如"Li7La3Zr2O12",为已知材料类型,分组信息可以为
    {
    "base":{
            "A":{"Li":7,"all":7},
            "B":{"La":3,"all":3},
            "C":{"Zr":2,"all":2},
            "D":{"O":12,"all":12},
            },
    "adsorb":{}
    }
    若原始化学式或分组后的化学式均无法符合已知材料配比，则每种元素均为单独位点。
    """
    res = ba.Q(prompt1)
    # print(res)
    prompt2 = f"需要分析的化学式为 {formula}"
    res = ba.Q(prompt2)
    # print(res)
    prompt3 = """
    将上述结果,按照各位点(A,B,C,...)配比的公约数尝试简化为最简整数配比,并分别将同位置的元素类别分别带入位点,获得多个不同的化学式及公约数。
    例如"SrCaTi2O6"的A的配比和(all)为4, B的配比和(all)为4, C的配比和(all)为12, A:B:C位点配比为4:4:12,可以化简为1:1:3的最简整数配比ABC3,公约数为4。
    注意不考虑元素的配比!!!仅分别将元素类别代入最简整数配比模板ABC3,获得化学式为"SrTiO3"与"CaTiO3"。
    返回所有可能的化学式(包含减去吸附原子的base化学式)的字典及公约数, 如下：
    
    {
    "base":{
        "A":{"Sr":3,"Ca":1,"all":4},
        "B":{"Ti":4,"all":4},
        "C":{"O":12,"all":12},
    },
    "adsorb":{},
    "temps":{"Sr3CaTi4O12":1,"SrTiO3":4,"CaTiO3":4}
    }
    
    掺杂元素adsorb, 直接给出元素及配比信息。
    注意：只返回结果字典,不要任何其他解释性信息。
    
    """
    res = ba.Q(prompt3)
    # print(res)
    prompt4 = "重新上述过程,检查两次结果一致性,只返回可以直接被json解析的结果字典,不要任何其他解释性信息。"
    res  = ba.Q(prompt4)
    res = rep_string(res)
    res = json.loads(res)
    
    base= res.get("base",{})
    ri= res.get("temps",{})
    adsorb = res.get("adsorb",{})

    
    msgs = []

    for k,v in ri.items():
        formula = k # 化学式
        v = int(v) # 超胞大小
        sup = {1:(1,1,1),2:(2,1,1),3:(3,1,1),4:(2,2,1),5:(5,1,1),6:(2,3,1),
                7:(7,1,1),8:(2,2,2),9:(3,3,1),10:(5,2,1),11:(11,1,1),12:(3,2,2),}
        msg = get_structure_dp_database(formula,space_group=None)
        
        if len(msg) == 0:
            pass
        else:
            for mi in msg:
                structure:Structure = mi.get("structure")
                structure2 = structure.copy()
                structure2 = structure2.make_supercell(sup.get(v))
                mi["structure"] = structure2
                mi["space_group"] = structure2.get_space_group_info()
                
                if v==1:
                    pass
                else:
                    for bk,bv in base.items():
                        if len(bv)==2:
                            bv.pop("all",None)
                            pass
                        else:
                            bv.pop("all",None)
                            names = list(bv.keys())
                            namess = []
                            for name,number in bv.items():
                                if isinstance(number, float):
                                    warnings.warn(f"Warning: Can't deal with float ratios {bv}, the result could be wrong.")

                                namess.extend([name]*int(number))
                                
                            names_all = structure2.symbol_set
                            
                            indexes = [i for i, name in enumerate(names_all) if name in names]
                            
                            if len(indexes) != len(namess):
                                pass
                            else:
                                for i in range(len(indexes)):
                                    structure2.replace(indexes[i], namess[i])
                
                if len(adsorb) != 0:
                    prompt5 = "吸附/掺杂元素种类及个数信息为："
                    prompt5 += str(adsorb)
                    prompt5 += f"请根据已有基底结构{structure2}, 估计合理的每个吸附/掺杂物原子的分数x,y,z坐标信息，各原子之间键长合理。"
                    prompt5 += """例如 {"O":2,"H":1} 的返回格式如:
                    {
                    "O": [[0.5, 0.22, 0.48], [0.5, 0.23, 0.5]], 
                    "H": [[0.5, 0.23, 0.52]]
                    }
                    """
                    prompt5 += "注意：只返回吸附/掺杂位点的结果字典,不要任何其他解释性信息。"
                    res = ba.Q(prompt5)
                    # print(res)
                    res = rep_string(res)
                    res = json.loads(res)
                    
                    res_add = {}
                    for resk,resv in res.items():
                        check = Element.is_valid_symbol(resk)
                            
                        if check and isinstance(resv, list):
                            for resvi in resv:
                                res_add[resk] = resvi
                else:
                    res_add = {}
                
                if len(res_add)>0:
                    for res_kk,res_vv in res_add.items():
                        structure2=structure2.append(res_kk,res_vv)
                        
                mi["adsorb"] = adsorb
                mi["base"] = base
                mi["species"] = structure2.symbol_set
                mi["abc"] = structure2.lattice.abc
                mi["angle"] = structure2.lattice.angles
                mi["fractional_coords"] = structure2.frac_coords.tolist()
                mi["reference_formula"] = mi.pop("formula")
                mi["reference_material_id"] = mi.pop("material_id")
                mi["poscar"] = Poscar(structure2)
                mi["poscar_str"] = str(mi["poscar"])
                
                msgs.append(mi)

                
    if len(msgs) == 0:
        raise ValueError("未能获取合适的结构模板。")
    
    with open('prompt/format.txt', 'r') as file:
        vt_format = file.read()
    return {"poscar_template":msgs[0]["poscar_str"], "vt_format":vt_format}







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

