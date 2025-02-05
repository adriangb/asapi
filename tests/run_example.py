#!/usr/bin/env -S uv run --script

import subprocess
import sys
import time
from pathlib import Path

import httpx

SCRIPT_PATH = Path(__file__).parent / "example.py"


def main() -> None:
    print("Starting server process...")
    server_process = subprocess.Popen(
        [sys.executable, SCRIPT_PATH, "3011"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    time.sleep(5)

    try:
        # Send request to the server using httpx
        with httpx.Client() as client:
            response = client.get("http://localhost:3011/echo/test")
            response.raise_for_status()

            # Check response
            expected_response = {"name": "test"}
            if response.json() != expected_response:
                print(f"Response was not as expected: {response.text}")
                server_process.terminate()
                sys.exit(1)
    except Exception as e:
        print(f"Error occurred during request: {e}")
        server_process.terminate()
        # get stdout and stderr
        try:
            stdout, stderr = server_process.communicate(timeout=5)
            return_code = server_process.returncode
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            print(f"return code: {return_code}")
        except subprocess.TimeoutExpired:
            print("Server failed to shut down within timeout period")
            server_process.kill()
        finally:
            sys.exit(1)

    print("Response validation successful")

    # Send SIGTERM to server
    print("Sending SIGTERM to server...")
    server_process.terminate()

    try:
        # Wait for process to complete and capture output
        stdout, stderr = server_process.communicate(timeout=5)
        return_code = server_process.returncode
        output = stdout + stderr

    except subprocess.TimeoutExpired:
        print("Server failed to shut down within timeout period")
        server_process.kill()
        sys.exit(1)

    # Check for required messages in output
    required_messages = ["Starting server", "Shutdown initiated", "Shutdown complete"]

    missing_messages = [msg for msg in required_messages if msg not in output]

    if missing_messages:
        print("Missing required messages in stdout:")
        for msg in missing_messages:
            print(f"- {msg}")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        sys.exit(1)

    # Check return code
    if return_code != 0:
        print(f"Server exited with unexpected return code: {return_code}")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        sys.exit(1)

    print("All tests passed successfully!")


if __name__ == "__main__":
    main()
