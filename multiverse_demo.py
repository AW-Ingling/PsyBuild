from multiverse import *

# Create some objects in design space and run space then inventory them in run space from design space
ds = DesignSpace()
tb_1 = TwinBase()
tb_2 = TwinBase()
tb_3 = TwinBase()
ds.inventory_run_space()

# Invoke a simple method on our twin object which accept pickelable objects as values
tb_3.echo("Hello World!")
tb_1.echo("A", "B")
tb_2.echo("One", "Two")
tb_2.echo("X")
tb_2.echo("Y")


# Invoke a simple method on our twin object which accepts instances of our twin class
tb_1.echo("Twin 1 printing Twin 1", tb_1)
tb_1.echo("Twin 1 printing Twin 2", tb_2)
tb_1.echo("Twin 1 printing Twin 3", tb_3)
tb_3.echo("Twin 3 printing Twin 1", tb_1)

# Echo only into design space
tb_1.echo_design("Hello", "Design World")

# Echo only into run space
tb_1.echo_run("Hello", "Run World")

# Echo a bunch of stuff
for i in range(1, 101):
    tb_1.echo(str(i))


