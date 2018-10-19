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
#
# Sample code for fetching leaf nodes
# https://stackoverflow.com/questions/21004181/how-to-get-leaf-nodes-of-a-tree-using-python
#
# Getting the class name from method decorators
# https://www.thecodeship.com/patterns/guide-to-python-function-decorators/
# https://stackoverflow.com/questions/2366713/can-a-python-decorator-of-an-instance-method-access-the-class
# https://stackoverflow.com/questions/306130/python-decorator-makes-function-forget-that-it-belongs-to-a-class
#
# How to find class of named tuple
# https://stackoverflow.com/questions/2166818/python-how-to-check-if-an-object-is-an-instance-of-a-namedtuple
#
# How to test if an object is pickleable:
# https://stackoverflow.com/questions/17872056/how-to-check-if-an-object-is-pickleable
#
# Python RPC:
# https://rpyc.readthedocs.io/en/latest/tutorial/tut3.html

# TO DO:
# - Enable inverse calls
# - Create synchronous calls which return results between spaces.
# - Transfer calls from design space to run space 
# - Exit processes gracefully.
# - Write tests
# - Make the spaces singletons
# - Create a design side thread to read back response from the run side.
# - Replace pipes with queues because we can not peek pipes.
# - Use decorators maximally.  Try using decorator wrappers to subclass.
# - Consider intercepting all object calls and auto translating to run space command by substituting our obj. refs
# - Implement a debug mode where all object execute in the same process?
# - Bundle commands so that client is always in a legal and matching state per frame
# - Test of pickleability when packing and unpacking inovocations
# - Look at an RPC library
# - Look at just using "eval"
# - Write a test module
# - Include named arguments



# CONSIDERATIONS:
#
# It should be possible to use a decorator to intercept all setter and other method calls, filter in only those
# not associated with the GUI, find the corresponding object in the real-time process and invoke those on it.
# 
#

import time
from collections import namedtuple
from multiprocessing import Process, Pipe

start_time_secs_global = time.time()

DESIGN_SPACE = 1
RUN_SPACE = 2

space_global = None

EXIT_IPC_COMMAND = 0
EVAL_IPC_COMMAND = 1
MESSAGE_IPC_COMMAND = 2
INSTANTIATION_IPC_COMMAND = 3
INVOCATION_IPC_COMMAND = 4
INVENTORY_IPC_COMMAND = 5

PROXY_FRAME_DELAY_SECS = 1/60

PackedMessage = namedtuple('PackedMessage', 'command, payload')
InvocationPayload = namedtuple('InvocationPayload', 'id method_name args')
InstantiationPayload = namedtuple('InstantiationPayload', 'class_name id')
IDArg = namedtuple('IDArg', 'id')


def pack_message(command, payload=None):
    return PackedMessage(command, payload)


def unpack_message(message):
    return message.command, message.payload


def make_create_twin_message(a_twinbase):
    message = pack_message(INSTANTIATION_IPC_COMMAND, a_twinbase.instantiation_descriptor)
    return message


def make_invocation_message(payload):
    message = pack_message(INVOCATION_IPC_COMMAND, payload)
    return message


def is_twin_arg(an_arg):
    isinstance(an_arg, IDArg)


def is_run_space():
    assert space_global, "Attempt to detect the space type before the space has been created."
    return type(space_global) is RunSpace


def is_design_space():
    assert space_global, "Attempt to detect the space type before the space has been created."
    return type(space_global) is DesignSpace


def space_constant_name():
    if type(space_global) is RunSpace:
        return "RUN_SPACE"
    elif type(space_global) is DesignSpace:
        return "DESIGN_SPACE"
    else:
        return None


def space_informal_name():
    if type(space_global) is RunSpace:
        return "RS"
    elif type(space_global) is DesignSpace:
        return "DS"
    else:
        return None

def secs():
    return time.time() - start_time_secs_global


class RunSpace:

    def __init__(self, pipe_connector):
        self.pipe_connector = pipe_connector
        self.id_to_obj_table = dict()
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
                elif command == INSTANTIATION_IPC_COMMAND:
                    twinbase_class = globals()[payload.class_name]
                    self.id_to_obj_table[payload.id] = twinbase_class()
                    #todo:reply here with the id of the new object for the inverse table in design space
                elif command == INVENTORY_IPC_COMMAND:
                    for key, value in self.id_to_obj_table.items():
                        print("key: %s, object: %s" % (key, value))
                elif command == INVOCATION_IPC_COMMAND:
                    object, bound_method, args = unpack_invocation_payload(payload)
                    apply_unpacked_invocation(bound_method, args)
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

    def send_message(self, message):
        self.design_connector.send(message)

    def create_runtime_twin(self, a_twinbase):
        message = make_create_twin_message(a_twinbase)
        self.design_connector.send(message)

    def inventory_design_space(self):
        pass

    def inventory_run_space(self):
        self.send_command(INVENTORY_IPC_COMMAND)


def pack_invocation_payload(method, args):
    # Find instances of TwinBase in the argument list and convert them to invocation descriptors
    converted_args = [arg.invocation_descriptor if issubclass(type(arg), TwinBase) else arg for arg in args]
    # Pack the id of the object, the invoked method and the converted args to a named tuple
    payload = InvocationPayload(id(args[0]), method.__name__, converted_args)
    return payload


def unpack_invocation_payload(payload):
    # Get the invoked object for its received ID
    object = space_global.id_to_obj_table[payload.id]
    # Get the object method reference by name inside the invocation object
    bound_method = getattr(object, payload.method_name)
    # Find and unpack any twin references inside the argument list
    args = [space_global.id_to_obj_table[arg.id] if isinstance(arg, IDArg) else arg for arg in payload.args]
    return object, bound_method, args


def apply_unpacked_invocation(bound_method, args):
    return bound_method(*args[1:])


def both_twin(twinbase_method):
    def wrapper(*argv):
        # invoke the decorated method in design space or run space
        local_result= twinbase_method(*argv)
        # conditionally invoke the run space instance remotely
        if is_design_space():
             # convert objects to references
             invocation_payload = pack_invocation_payload(twinbase_method, argv)
             invocation_method = make_invocation_message(invocation_payload)
             # transmist the invocation to the twin in run space
             space_global.send_message(invocation_method)
        return local_result
    return wrapper


def design_twin(twinbase_method):
    def wrapper(*argv):
        return twinbase_method(*argv)
    return wrapper


def run_twin(twinbase_method):
    def wrapper(*argv):
        if is_design_space():
            # convert objects to references
            invocation_payload = pack_invocation_payload(twinbase_method, argv)
            invocation_method = make_invocation_message(invocation_payload)
            # transmit the invocation to the twin in run space
            space_global.send_message(invocation_method)
        # invoke the decorated method only in run space
        if is_run_space():
            return twinbase_method(*argv)
    return wrapper


class TwinBase:

    def __init__(self):
        assert space_global, "Attempt to instantiate a TwinBase kind without the design space portal."
        if is_design_space():
            # instantiate a matched instance of ourselves in the runtime space
            space_global.create_runtime_twin(self)
            #TODO: receive twin ID from runtime space and store it in the space object table.

    @property
    def instantiation_descriptor(self):
        descriptor = InstantiationPayload(type(self).__name__, id(self))
        return descriptor

    @property
    def invocation_descriptor(self):
        descriptor = IDArg(id(self))
        return descriptor

    def _echo(self, *argv):
        for index, arg in enumerate(argv):
            print("%s %s echo: %s, %s" % (str(secs()), str(space_informal_name()), str(index), str(arg)))

    @both_twin
    def echo(self, *argv):
        self._echo(*argv)

    @design_twin
    def echo_design(self, *argv):
        self._echo(*argv)

    @run_twin
    def echo_run(self, *argv):
        self._echo(*argv)







