import runner
from hypothesis import settings, given
from hypothesis.strategies import just
code = """fun main(args: Array<String>) {
    println("Hello, World!")
}
"""

@given(just(code))
@settings(deadline=None)
def compilertest(s):
    output1 = runner.run(s, "kotlinc-jvm")
    output2 = runner.run(s, "kotlinc")
    assert output1 == output2

compilertest()