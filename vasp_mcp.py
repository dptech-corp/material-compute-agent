from mcp.server.fastmcp import FastMCP
from pydantic import Field
import httpx
import json
import os
import logging
import mcp
import subprocess
import shutil
import time
import re
import asyncio
import zipfile

# 初始化FastMCP实例
mcp = FastMCP()

@mcp.tool(name="submit_vasp_job", description="提交VASP计算任务到计算集群")
async def submit_vasp_job(
    calcdir: str = Field(description="计算目录的完整路径，包含VASP输入文件")
) -> str:
    """提交VASP计算任务
    
    Args:
        calcdir (str): 计算目录的完整路径，需包含必要的VASP输入文件
        
    Returns:
        str: 提交成功返回任务ID，失败返回错误信息
        
    Raises:
        FileNotFoundError: 当目录不存在或无法访问时
        Exception: 复制文件或提交任务失败时
    """
    current_dir = os.getcwd()
    if not os.path.exists(calcdir):
        if not os.path.exists(os.path.join("material-compute-agent", calcdir)):
            return f"当前路径：{current_dir}，错误：计算目录不存在，请检查路径是否正确"
        else:
            calcdir = os.path.join("material-compute-agent", calcdir)
    
    try:
        shutil.copy("job.json", os.path.join(calcdir, "job.json"))
    except Exception as e:
        return f"错误：无法复制job.json文件 - {str(e)}"

    bohr_path = subprocess.run(
        ['which', 'bohr'], 
        stdout=subprocess.PIPE, 
        text=True
    ).stdout.strip()
    
    if not bohr_path:
        return "错误：找不到 bohr 命令，请确保已正确安装"
        
    command = f'cd {calcdir} && {bohr_path} job submit -i job.json -p ./'
    result = subprocess.run(
        ['/bin/zsh', '-c', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 添加错误处理
    if result.returncode != 0:
        return f"错误：任务提交失败 - {result.stderr}"
        
    job_match = re.search(r'JobId:\s*(\d+)', result.stdout)
    if not job_match:
        return "错误：无法获取任务ID"
        
    jobid = job_match.group(1)
    return f"✅ VASP计算任务已提交成功，任务ID：{jobid}"



@mcp.tool(name="show_vasp_config", description="显示VASP计算的输入配置文件内容")
async def show_vasp_config(
    calcdir: str = Field(description="计算目录的完整路径，包含INCAR和POSCAR文件")
) -> dict:
    """向人类展示显示VASP计算的关键输入配置文件内容
    
    Args:
        calcdir (str): 计算目录的完整路径
        
    Returns:
        dict: 包含INCAR和POSCAR文件内容的字典
        
    Raises:
        FileNotFoundError: 当目录或配置文件不存在时
    """
    if not os.path.exists(calcdir):
        return {"error": "计算目录不存在"}
        
    result = {}
    for config in ["INCAR"]:
        config_path = os.path.join(calcdir, config)
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                result[config] = f.read()
        else:
            result[config] = f"错误：{config}文件不存在"
    return result



@mcp.tool(name="rewrite_vasp_config", description="重写VASP计算的输入配置文件内容")
async def rewrite_vasp_config(
    calcdir: str = Field(description="计算目录的完整路径，包含INCAR和POSCAR文件"),
    config: str = Field(description="要重写的配置文件名称，例如 'INCAR' 或 'POSCAR'"),
    new_content: str = Field(description="新的配置文件内容")
) -> dict:
    """
    重写VASP计算的关键输入配置文件内容

    Args:
        calcdir (str): 计算目录的完整路径，应该包含VASP的配置文件（如INCAR、POSCAR）。
        config (str): 要重写的配置文件名称，例如 'INCAR' 或 'POSCAR'。
        new_content (str): 用于重写的新的配置文件内容。

    Returns:
        dict: 操作结果的字典。如果成功，返回成功消息；否则返回错误说明。

    Raises:
        FileNotFoundError: 当目录或指定配置文件不存在时。
    """
    # 检查计算目录是否存在
    if not os.path.exists(calcdir):
        return {"error": "计算目录不存在"}
    
    # 构造目标配置文件的完整路径
    config_path = os.path.join(calcdir, config)
    
    # 如果目标配置文件不存在，则返回错误信息
    if not os.path.exists(config_path):
        return {"error": f"错误：{config}文件不存在"}
    
    # 尝试重写该配置文件
    try:
        with open(config_path, "w") as f:
            f.write(new_content)
        return {"success": True, "message": f"{config}文件已成功重写", "new_content": new_content}
    except Exception as e:
        return {"error": f"重写{config}文件失败: {str(e)}"}


@mcp.tool(name="monitor_vasp_job", description="监控VASP计算任务状态并下载结果")
async def monitor_vasp_job(
    job_id: int = Field(description="VASP计算任务的ID编号")
) -> str:
    """监控VASP计算任务的执行状态并在完成后下载结果"""
    print(f"🚀 开始监控任务 {job_id} 的执行状态...")

    # 查找 bohr 路径
    bohr_path = subprocess.run(
        ['which', 'bohr'],
        stdout=subprocess.PIPE,
        text=True
    ).stdout.strip()

    if not bohr_path:
        return "❌ 错误：找不到 bohr 命令，请确保已正确安装并在环境变量中"

    while True:
        try:
            # 查询任务状态
            describe_proc = await asyncio.create_subprocess_exec(
                bohr_path, "job", "describe", "-j", str(job_id), "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            stdout, stderr = await describe_proc.communicate()

            if describe_proc.returncode != 0:
                return f"❌ 状态查询失败：{stderr.decode().strip()}"

            job_info = json.loads(stdout.decode())[0]
            status = job_info["statusStr"]
            print(f"⏱ 当前状态：{status}")

            if status == "Finished":
                print("✅ 任务完成，开始下载结果")

                # 下载任务结果
                download_proc = await asyncio.create_subprocess_exec(
                    bohr_path, "job", "download", "-j", str(job_id),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=os.environ.copy()
                )
                out, err = await download_proc.communicate()

                if download_proc.returncode != 0:
                    return f"❌ 结果下载失败：{err.decode().strip()}"

                # 解压下载结果
                base_dir = os.getcwd()
                zip_path = os.path.join(base_dir, f"{job_id}/out.zip")
                extract_dir = os.path.join(base_dir, f"{job_id}/out")
                os.makedirs(extract_dir, exist_ok=True)

                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    return f"✅ 结果已下载并解压，vasprun.xml路径：{os.path.join(extract_dir, 'vasprun.xml')}"
                except Exception as e:
                    return f"❌ 结果文件解压失败：{str(e)}"

            elif status in ["Failed", "Terminated"]:
                return f"⚠️ 任务异常终止（状态：{status}）"

            await asyncio.sleep(10)

        except Exception as e:
            return f"❌ 发生未预期的错误：{str(e)}"


        
if __name__ == "__main__":
    mcp.run(transport='stdio')