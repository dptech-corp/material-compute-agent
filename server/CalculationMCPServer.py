from dp.agent.adapter.camel.server.CalculationMCPServer import CalculationMCPServer
import subprocess
import os   
import time
mcp = CalculationMCPServer("Demo")


@mcp.tool()
def vasp_job() -> dict:
    """
    Submit VASP calculation jobs in each subdirectory under the 'tmp' folder.

    This function changes the current working directory to 'tmp', locates all subdirectories,
    and runs the VASP job in each one by executing a shell command. After execution,
    it returns to the original directory.

    Returns:
        dict: A dictionary with 'status' and 'message'. Returns success if all jobs are launched.
              On failure, raises an exception with error details.

    Raises:
        FileNotFoundError: If the 'tmp' directory does not exist or cannot be accessed.
        Exception: If no subdirectories are found or if job execution fails.

    Example:
        result = vasp_job()
        e.g., "All jobs submitted successfully 🎉"
    """
    start_dir = os.getcwd()

    try:
        os.chdir('tmp')

        subdirs = [d for d in os.listdir() if os.path.isdir(d)]
        if not subdirs:
            raise Exception("No subdirectories found in 'tmp' for VASP jobs.")

        for subdir in subdirs:
            print(f"Launching VASP in subdirectory: {subdir}...")
            os.chdir(subdir)

            # Customize this command to your HPC environment
            command = (
                "source /opt/intel/oneapi/setvars.sh && "
                "mpirun -n 32 vasp_std > vasp.log 2>&1"
            )

            subprocess.run(['bash', '-c', command], check=True)
            os.chdir('..')
            print(f"Finished executing in: {subdir}")

    except Exception as e:
        os.chdir(start_dir)
        log = open("log", "r").read()
        return {"status": "error", "message": f"Failed to submit VASP jobs: {e}\n{log}"}
    finally:
        os.chdir(start_dir)
    return {"status": "success", "message": "All VASP jobs submitted successfully 🎉"}


if __name__ == "__main__":
    mcp.run(transport="sse")
