"""Main Loop for the server side"""

import sys

# Import required RPC modules
import protobuf.socketrpc.server as server
import impl_ctl

def main():
    control_service = impl_ctl.ImplCtl()
    srv = server.SocketRpcServer(10021, host='0.0.0.0')
    srv.registerService(control_service)
    srv.run()

if __name__ == "__main__":
    main()
