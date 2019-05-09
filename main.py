import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import just, text, characters, composite, integers
import random
import string
import time


names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)

numbers = integers()

@composite
def projects(draw):
    name = draw(names)
    code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }
    """
    return code.replace("World", name)


def genCode(draw):
    fuel = 25
    string_code = ""
    list = []
    while(fuel > 0):
        temps, templist = genExp(draw, list)
        list = templist
        string_code += temps
        fuel -= 1
    return string_code

def genExp(draw, list):
    r = random.randint(1, 6)
    if True:
        s, vn = genVariable(draw, list)
        return s, vn

def genVariable(draw, list):
    newName = True
    name = ""
    while newName:
        name = draw(names)
        if name not in list:
            newName = False
            list.append(name)
    return ('var ' + name + ' = ' + str(draw(numbers)) + ';\n\r'), list

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

@composite
def projectsv2(draw):
    gen = genCode(draw)
    code = """
    fun main(args: Array<String>) {
        input
    }
    """
    return code.replace("input", gen)

@given(projectsv2())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=20)
def compilertest(s):
    dt = datetime.now()
    name = "out/folder" + (str(dt.microsecond))
    print("run")
    output1 = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(s, "kotlinc-native", outputDirectory= name + "-native")
    assert output1 == output2
    time.sleep(1)
compilertest()

