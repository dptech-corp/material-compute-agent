# Science Agent SDK

This is DP Tech's Science Agent SDK, providing a command-line tool `dp-agent` for managing scientific computing tasks.

## Installation

### Linux/Mac

```bash
curl -sSL https://raw.githubusercontent.com/dptech-corp/science-agent-sdk/refs/heads/master/install.sh | bash
```

### Windows

In PowerShell, run:

```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/dptech-corp/science-agent-sdk/refs/heads/master/install.sh -OutFile install.sh
bash install.sh
```

## Usage

After installation, you can use the following commands:

### Fetch Scaffolding

```bash
dp-agent fetch scaffolding
```

### Fetch Configuration

```bash
dp-agent fetch config
```

This command downloads the .env file and replaces dynamic variables such as MQTT_DEVICE_ID.
Note: For security reasons, this feature is only available in internal network environments. Other environments require manual configuration.

### Run Lab Environment

```bash
dp-agent run-lab
```

### Run Cloud Environment

```bash
dp-agent run-cloud
```

### Run Agent

```bash
dp-agent run-agent
```

### Debug Cloud Environment

```bash
dp-agent debug-cloud
```

## Development Notes

This SDK provides a client-server architecture for submitting and managing scientific computing tasks. For detailed API documentation, please refer to the comments in the code.
