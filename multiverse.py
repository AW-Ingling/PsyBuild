# multiverse.py


# REFERENCES:
#
# Multiprocessing:
# https://docs.python.org/3.6/library/multiprocessing.html
#
# Queues:
# https://docs.python.org/3.6/library/queue.html#queue.Queue
#
# How to override attribute setting (to communicate values to run space), override setattr
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
# - Transfer calls from design space to run space 
# - Rename "space" to "space"
# - Exit processes gracefully.
# - Write tests
# - Make the spaces singletons
# - Create a design side thread to read back response from the run side.
# - Replace pipes with queues because we can not peek pipes.
# - Use decorators maximally.  Try using decorator wrappers to subclass.
# - Consider intercepting all object calls and auto translating to run space command by substituting our obj. refs
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


DESIGN_SPACE = 0
RUN_SPACE = 1

space_global = None

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


def is_run_space():
    assert space_global, "Attempt to detect the space type before the space has been created."
    return type(space_global) is RunSpace


def is_design_space():
    assert space_global, "Attempt to detect the space type before the space has been created."
    return type(space_global) is DesignSpace


class RunSpace:

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
                    #todo:reply here with the id of the new object for the inverse table in design space
                elif command == INVENTORY_IPC_COMMAND:
                    for key, value in self.design_id_to_obj_table.items():
                        print("key: %s, object: %s" % (key, value))
                else:
                    assert False, "Unknown command received from design space."
            time.sleep(PROXY_FRAME_DELAY_SECS)


def start_run_space(pipe_connector):
    global space_global
    space_global = RunSpace(pipe_connector)
    space_global.start_read_eval_loop()


class DesignSpace:

    def __init__(self):
        # anchor ourselves by a top level variable reference to prevent garbage collection
        global space_global
        space_global = self
        # init state
        self.design_connector = None
        self.run_connector = None
        self.run_space_process = None
        # Launch the run space
        self.start_run_space();

    def start_run_space(self):
        self.design_connector, self.run_connector = Pipe()
        self.run_space_process = Process(target=start_run_space, args=(self.run_connector,))
        self.run_space_process.start()

    def send_command(self, command, payload=None):
        message = pack_message(command, payload)
        self.design_connector.send(message)
    #
    # def send_message(self, message):
    #     self.design_connector.send(message)

    def create_runtime_twinbase(self, a_twinbase):
        message = make_twinbase_message(a_twinbase)
        self.design_connector.send(message)

    def inventory_design_space(self):
        pass

    def inventory_run_space(self):
        self.send_command(INVENTORY_IPC_COMMAND)



class TwinBase:

    def __init__(self):
        assert space_global, "Attempt to instantiate a TwinBase kind without the design space portal."
        if is_design_space():
            # instantiate a matched instance of ourselves in the runtime space
            space_global.create_runtime_twinbase(self)
            #TODO: receive twin ID from runtime space and store it in the space object table.











