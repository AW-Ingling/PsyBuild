from multiverse import *

# Create some objects in design space and run space then inventory them in run space from design space
ds = DesignSpace()
tb_1 = TwinBase()
tb_2 = TwinBase()
tb_3 = TwinBase()
ds.inventory_run_space()

# Invoke a simple method on our twin object which accept pickelable objects as values
tb_1.print_test("Hello", "World")
tb_2.print_text("Hello", "World again")
tb_3.print_text("Hello", "World yet again")

# Invoke a simple method on our twin object which accepts instances of our twin class
tb_1.print_test("Twin 1 printing Twin 1", tb_1)
tb_1.print_test("Twin 1 printing Twin 2", tb_2)
tb_1.print_test("Twin 1 printing Twin 3", tb_3)
tb_3.print_test("Twin 3 printing Twin 1", tb_1)


