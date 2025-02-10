import argparse
from ssh_connection import SshConnection

def main():
    parser = argparse.ArgumentParser(description="SSH Command Runner")
    parser.add_argument('source', choices=['local', 'remote'], help="Source of the command execution (local or remote)")
    parser.add_argument('command', help="The command to run")
    parser.add_argument('--username', help="Username for the SSH server, required with remote")
    parser.add_argument('--password', help="Password for the SSH server, required with remote (use either this or private_key)")
    parser.add_argument('--private_key', help="Path to private key for the SSH server, required with remote (use either this or passowrd)")
    parser.add_argument('--server', default="alma.icr.ac.uk", help="Remote server address (default: alma.icr.ac.uk)")
    parser.add_argument('--df', action='store_true', help="Return the output as pandas DataFrame if set")
    parser.add_argument('--sep', default=',', help="Use selected separator when reading from csv")

    args = parser.parse_args()
 
    # Check for valid authentication method (either password or private_key)
    if args.source=="remote":
        if not args.password and not args.private_key:
            raise ValueError("You must specify either --password or --private_key for remote connections.")
        if args.password and args.private_key:
            raise ValueError("You cannot specify both --password and --private_key at the same time.")

    # Create SSH connection based on authentication method
    if args.password:
        ssh = SshConnection(args.source, args.server, username=args.username, password=args.password)
    else:  # Use private key
        ssh = SshConnection(args.source, args.server, username=args.username, key_path=args.private_key)
    
    result = ssh.run_cmd(cmd=args.command, is_string=not args.df, sep=args.sep)

    # Handle unpacking based on length
    if len(result) == 2:
        output, err = result
    else:
        output, err = result, None

    if err:
        print(f"Error: {err}")
    else:
        print(output)

if __name__ == "__main__":
    main()

