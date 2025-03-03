import argparse
from local import LocalFileReader
from ssh import SshConnection

def main():
    parser = argparse.ArgumentParser(description="File Reader")
    parser.add_argument("--local", help="Path to local file", type=str)
    parser.add_argument("--ssh", help="Path to remote file", type=str)
    parser.add_argument("--host", help="SSH server", type=str)
    parser.add_argument("--user", help="SSH Username", type=str)
    parser.add_argument("--password", help="SSH Password", type=str)
    parser.add_argument("--cmd", help="Command to execute", type=str)
    
    args = parser.parse_args()
    
    if args.local:
        reader = LocalFileReader()
        content = reader.read_file(args.local)
        if content:
            print("Local File Content:\n", content)
    elif args.ssh and args.host and args.user and args.password:
        reader = SshConnection(args.host, args.user, args.password)
        content = reader.read_file(args.ssh)
        if content:
            print("Remote File Content:\n", content)
    elif args.cmd:
        reader = LocalFileReader()
        output = reader.run_cmd(args.cmd)
        if output:
            print("Command Output:\n", output)
    else:
        print("Invalid arguments. Provide either --local or --ssh with SSH details, or --cmd for command execution.")

if __name__ == "__main__":
    main()