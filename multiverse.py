# multiverse.py


# REFERENCES:
#
# Multiprocessing:
# https://docs.python.org/3.6/library/multiprocessing.html
#
# Queues:
# https://docs.python.org/3.6/library/queue.html#queue.Queue
#
# How to override attribute setting (to communicate values to run universe), override setattr
# https://docs.python.org/dev/reference/datamodel.html#object.__setattr__
#
# How to get a python object by ID
# https://stackoverflow.com/questions/1396668/get-object-by-id
#
# How to intercept method calls
# https://stackoverflow.com/questions/2704434/intercept-method-calls-in-python
#
# Examples of decorators
# https://wiki.python.org/moin/PythonDecoratorLibrary#Property_Definition
#
# How to write method decorators
# https://stackoverflow.com/questions/11731136/python-class-method-decorator-with-self-arguments

# TO DO:
# - Replace pipes with queues because we can not peek pipes.
# - Use decorators maximally.  Try using decorator wrappers to subclass.
# - Consider intercepting all object calls and auto translating to run universe command by substituting our obj. refs
# - Implement a debug mode where all object execute in the same process?
# - Bundle commands so that client is always in a legal and matching state per frame

# CONSIDERATIONS:
#
# It should be possible to use a decorator to intercept all setter and other method calls, filter in only those
# not associated with the GUI, find the corresponding object in the real-time process and invoke those on it.
# 
#

import time
from multiprocessing import Process, Pipe

DESIGN_UNIVERSE = 0
RUN_UNIVERSE = 1

run_universe = None

EXIT_IPC_COMMAND = 0
EVAL_IPC_COMMAND = 1
MESSAGE_IPC_COMMAND = 2

PROXY_FRAME_DELAY_SECS = 1/60


def pack_message(command, payload):
    return (command, payload)

def unpack_message(message):
    return message[0], message[1]


class RunUniverse:

    def __init__(self, pipe_connector):
        self.pipe_connector = pipe_connector
        self.design_id_to_obj_table = dict()
        self.run_read_loop = True

    def start_read_eval_loop(self):
        while self.run_read_loop:
            if self.pipe_connector.poll():
                message = self.pipe_connector.recv()
                command, payload = unpack_message(message)
                if command == EXIT_IPC_COMMAND:
                    self.run_read_loop = False
                elif command == MESSAGE_IPC_COMMAND:
                    print("message: " + str(payload))
                elif command == EVAL_IPC_COMMAND:
                    print("EVAL_IPC_COMMAND unimplemented")
                else:
                    assert False, "Unrecogmized command received by client"
            time.sleep(PROXY_FRAME_DELAY_SECS)


def start_run_portal(pipe_connector):
    global run_universe
    run_universe = RunUniverse(pipe_connector)
    run_universe.start_read_eval_loop()


class DesignPortal:

    def __init__(self):
        self.design_connector = None
        self.run_connector = None
        self.run_universe_process = None

    def start_run_unviverse(self):
        self.design_connector, self.run_connector = Pipe()
        self.run_universe_process = Process(target=start_run_portal, args=(self.run_connector,))
        self.run_universe_process.start()

    def send_command(self, command, payload=None):
        message = pack_message(command, payload)
        self.design_connector.send(message)

    def send_message(self, message):
        self.design_connector.send(message)



# class TwinBase:
#
#     def __init__(self):
#         self.design_id = id(self)
#         self.run_id = None






