"""
Example of using the science-agent-sdk lab functionality.
"""
import signal
import sys
from src.dp.agent.lab import DeviceTwin, TescanDevice

def signal_handler(sig, frame):
    """Handle SIGINT signal to gracefully shutdown."""
    print("Shutting down...")
    sys.exit(0)

def main():
    """Start the lab services."""
    print("Starting Device Twin Lab Services...")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create device instance
    tescan_device = TescanDevice()
    
    # Create device twin
    device_twin = DeviceTwin(tescan_device)
    
    # Run device twin
    device_twin.run()

if __name__ == "__main__":
    main() 