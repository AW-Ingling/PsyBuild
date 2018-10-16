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
# - Rename "universe" to "space"
# - Exit processes gracefully.
# - Write tests
# - Make the spaces singletons
# - Create a design side thread to read back response from the run side.
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
from collections import namedtuple
from multiprocessing import Process, Pipe


DESIGN_UNIVERSE = 0
RUN_UNIVERSE = 1

universe_global = None

EXIT_IPC_COMMAND = 0
EVAL_IPC_COMMAND = 1
MESSAGE_IPC_COMMAND = 2
CREATE_TWINBASE_IPC_COMMAND = 3
INVENTORY_IPC_COMMAND = 4

PROXY_FRAME_DELAY_SECS = 1/60

TwinBaseDescriptor = namedtuple('TwinBaseDescriptor', 'class_name id')
PackedMessage = namedtuple('PackedMessage', 'command, payload')

def pack_message(command, payload=None):
    return PackedMessage(command, payload)


def unpack_message(message):
    return message.command, message.payload


def make_twinbase_descriptor(a_twinbase):
    assert issubclass(type(a_twinbase), TwinBase)
    descriptor = TwinBaseDescriptor(type(a_twinbase).__name__, id(a_twinbase))
    return descriptor


def make_twinbase_message(a_twinbase):
    payload =  make_twinbase_descriptor(a_twinbase)
    message = pack_message(CREATE_TWINBASE_IPC_COMMAND, payload)
    return message


def is_run_universe():
    assert universe_global, "Attempt to detect the universe type before the universe has been created."
    return type(universe_global) is RunUniverse


def is_design_universe():
    assert universe_global, "Attempt to detect the universe type before the universe has been created."
    return type(universe_global) is DesignUniverse


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
                elif command == CREATE_TWINBASE_IPC_COMMAND:
                    twinbase_class = globals()[payload.class_name]
                    self.design_id_to_obj_table[payload.id] = twinbase_class()
                    #todo:reply here with the id of the new object for the inverse table in design universe
                elif command == INVENTORY_IPC_COMMAND:
                    for key, value in self.design_id_to_obj_table.items():
                        print("key: %s, object: %s" % (key, value))
                else:
                    assert False, "Unknown command received from design universe."
            time.sleep(PROXY_FRAME_DELAY_SECS)


def start_run_universe(pipe_connector):
    global universe_global
    universe_global = RunUniverse(pipe_connector)
    universe_global.start_read_eval_loop()


class DesignUniverse:

    def __init__(self):
        # anchor ourselves by a top level variable reference to prevent garbage collection
        global universe_global
        universe_global = self
        # init state
        self.design_connector = None
        self.run_connector = None
        self.run_universe_process = None
        # Launch the run universe
        self.start_run_universe();

    def start_run_universe(self):
        self.design_connector, self.run_connector = Pipe()
        self.run_universe_process = Process(target=start_run_universe, args=(self.run_connector,))
        self.run_universe_process.start()

    def send_command(self, command, payload=None):
        message = pack_message(command, payload)
        self.design_connector.send(message)
    #
    # def send_message(self, message):
    #     self.design_connector.send(message)

    def create_runtime_twinbase(self, a_twinbase):
        message = make_twinbase_message(a_twinbase)
        self.design_connector.send(message)

    def inventory_design_universe(self):
        pass

    def inventory_run_universe(self):
        self.send_command(INVENTORY_IPC_COMMAND)



class TwinBase:

    def __init__(self):
        assert universe_global, "Attempt to instantiate a TwinBase kind without the design space portal."
        if is_design_universe():
            # instantiate a matched instance of ourselves in the runtime universe
            universe_global.create_runtime_twinbase(self)
            #TODO: receive twin ID from runtime universe and store it in the universe object table.











