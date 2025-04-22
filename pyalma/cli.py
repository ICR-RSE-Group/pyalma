import argparse
from .local import LocalFileReader
from .ssh import SshClient
from importlib.metadata import version, PackageNotFoundError

def main():
    """
    Entry point for the CLI-based file reader.

    This script allows users to perform the following actions:
        - Read a local file using the ``--local`` flag.
        - Connect to a remote server via SSH to read a file using the ``--ssh``, ``--host``, ``--user``, and ``--password`` flags.
        - Execute a shell command locally using the ``--cmd`` flag.
        - Check the installed version of the package with ``--version``.

    Example:

    To read a local file:
        - python -m pyalma.main --local ./data.txt

    To read a remote file via SSH:
        - python -m pyalma.main --ssh /remote/path.txt --host alma.icr.ac.uk --user myuser --password secret

    To run a local command:
        - python -m pyalma.main --cmd "ls -l"

    :return: None
    :rtype: NoneType
    """

    # Attempt to get the current package version
    try:
        pkg_version = version("pyalma")
    except PackageNotFoundError:
        pkg_version = "unknown"

    # Argument parser setup
    parser = argparse.ArgumentParser(description="File Reader CLI")
    parser.add_argument("--local", help="Path to local file", type=str)
    parser.add_argument("--ssh", help="Path to remote file", type=str)
    parser.add_argument("--host", help="SSH server", type=str)
    parser.add_argument("--user", help="SSH Username", type=str)
    parser.add_argument("--password", help="SSH Password", type=str)
    parser.add_argument("--cmd", help="Command to execute locally", type=str)
    parser.add_argument("--version", action="version", version=f"%(prog)s {pkg_version}")

    args = parser.parse_args()

    # Local file reading
    if args.local:
        reader = LocalFileReader()
        content = reader.read_file(args.local)
        if content:
            print("📄 Local File Content:\n", content)

    # Remote SSH file reading
    elif args.ssh and args.host and args.user and args.password:
        reader = SshClient(args.host, args.user, args.password)
        content = reader.read_file(args.ssh)
        if content:
            print("🌐 Remote File Content:\n", content)

    # Local command execution
    elif args.cmd:
        reader = LocalFileReader()
        output = reader.run_cmd(args.cmd)
        if output:
            print("🖥️ Command Output:\n", output)

    # If no valid combination of arguments is provided
    else:
        print("❌ Invalid arguments. Please provide either:\n"
              "  --local <path>\n"
              "  OR --ssh <path> --host <host> --user <user> --password <pass>\n"
              "  OR --cmd <command>")

if __name__ == "__main__":
    main()
