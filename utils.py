import json
import os

def edit_job_json(project_id: int, image_address: str = "registry.dp.tech/dptech/vasp:5.4.4", output_file: str = "job.json") -> dict:
    """
    编辑或创建 job.json 文件，设置项目编号和镜像信息
    
    Args:
        project_id (int): 项目编号，例如 21128
        image_address (str): 镜像地址，默认为 "registry.dp.tech/dptech/vasp:5.4.4"
        output_file (str): 输出文件名，默认为 "job.json"
    
    Returns:
        dict: 更新后的配置内容
    """
    # 默认配置
    default_config = {
        "job_name": "Bohrium-VASP",
        "job_type": "container",
        "command": "source /opt/intel/oneapi/setvars.sh && mpirun -n 32 vasp_std ",
        "log_file": "tmp_log",
        "backward_files": [],
        "project_id": project_id,
        "platform": "ali",
        "machine_type": "c32_m32_cpu",
        "image_address": image_address
    }
    
    try:
        # 如果文件存在，读取现有配置
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                config = json.load(f)
                # 更新配置
                config["project_id"] = project_id
                config["image_address"] = image_address
        else:
            config = default_config
        
        # 写入文件
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"✅ 成功更新 {output_file}")
        print(f"项目编号: {project_id}")
        print(f"镜像地址: {image_address}")
        
        return config
        
    except Exception as e:
        print(f"❌ 更新 {output_file} 失败: {str(e)}")
        return {}