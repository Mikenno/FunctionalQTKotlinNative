import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import just, text, characters, composite, integers, random_module
import random
import string
import time


names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)
numbers = integers()

depth = 1

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
    variables = []
    while(fuel > 0):
        newCode, newVariableList = genExp(draw, variables)
        variables = newVariableList
        string_code += newCode
        fuel -= 1
    return string_code

def genExp(draw, variables):
    r = random.randint(1, 2)
    if r == 1:
        generatedCode, variableList = genVariable(draw, variables)
        return generatedCode, variableList
    elif r == 2:
        return genVariableChange(draw, variables)

def genVariableChange(draw, variables):
    if len(variables) == 0:
        return genVariable(draw, variables)

    index = random.randint(0, len(variables))
    variableName = variables[index-1]
    return (depth*"\t" + variableName + "+=" + str(draw(numbers)) + ";\n"), variables

def genVariable(draw, variables):
    newName = True
    name = ""
    while newName:
        name = draw(names)
        if name not in variables:
            newName = False
            variables.append(name)
    return (depth*"\t" + 'var ' + name + ' = ' + str(draw(numbers)) + ';\n'), variables

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

@composite
def projectsv2(draw):
    gen = genCode(draw)
    code = """fun main(args: Array<String>) {
input}
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

