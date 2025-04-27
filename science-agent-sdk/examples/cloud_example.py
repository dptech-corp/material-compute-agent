"""
Example of using the science-agent-sdk cloud functionality.
"""
import signal
import sys
from dp.agent.cloud import mcp, get_mqtt_cloud_instance
from dp.agent.lab.device import TescanDevice, register_mcp_tools
from dp.agent.lab.device.device import register_mcp_tools

def signal_handler(sig, frame):
    """Handle SIGINT signal to gracefully shutdown."""
    print("Shutting down...")
    get_mqtt_cloud_instance().stop()
    sys.exit(0)

def main():
    """Start the cloud services."""
    print("Starting Tescan Device Twin Cloud Services...")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create device instance
    device = TescanDevice(mcp, device)
    
    # Register device tools
    register_mcp_tools(device)
    
    # Start MCP server
    print("Starting MCP server...")
    mcp.run(transport="sse")

if __name__ == "__main__":
    main() 