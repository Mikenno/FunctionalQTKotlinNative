from hypothesis._strategies import randoms, sampled_from, one_of, recursive, builds

import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck, assume, Verbosity
from hypothesis.strategies import just, text, characters, composite, integers, random_module
import math
import os
import random
import string
from datetime import datetime

from hypothesis import assume, Verbosity
from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import text, characters, composite, integers, decimals

import runner

NUMBER_TYPES = ["Long", "Int", "Double"]
COMPATIBLE_TYPES = {"String": ["String"] + NUMBER_TYPES,
                    "Long": NUMBER_TYPES,
                    "Int": NUMBER_TYPES,
                    "Double": NUMBER_TYPES}

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)

long = integers(min_value=-math.pow(2, 63), max_value=(math.pow(2, 63) - 1))
integer = integers(min_value=-math.pow(2, 31), max_value=math.pow(2, 31) - 1)
positiveInteger = integers(min_value=0, max_value=math.pow(2, 63) - 1)
negativeInteger = integers(min_value=-math.pow(2, 63), max_value=0)
double = decimals(allow_infinity=False, allow_nan=False)

functionParametersCount = integers(min_value=0, max_value=10)
fuelGen = integers(min_value=1, max_value=200)


@composite
def projects(draw):
    name = draw(names)
    code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }
    """
    return code.replace("World", name)


def genCode(draw, variables, functions, globalfuntions, properties):
    string_code = ""
    while properties["fuel"] > 0:
        newCode, newVariableList, functions, globalfuntions = draw(genExp(variables, functions, globalfuntions, properties))
        variables = newVariableList
        string_code += newCode
        properties["fuel"] -= 1
    return string_code, variables, functions, globalfuntions


@composite
def genLoop(draw, variables, functions, globalfuntions, properties):
    startValue = draw(integers(max_value=math.pow(2, 8), min_value=-math.pow(2, 8)))

    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    varName = draw(names.filter(lambda x: x not in variableNames))
    endValue = draw(integers(max_value=math.pow(2, 8), min_value=-math.pow(2, 8)))

    localProps = properties.copy()
    localProps["fuel"] = draw(integers(min_value=1, max_value=min([20, properties["fuel"]])))
    properties["fuel"] -= localProps["fuel"]
    finalCode = ""

    localVars = variables.copy()
    localVars += [(varName, "Int", False)]
    localFuncs = functions.copy()

    while localProps["fuel"] > 0:
        code, vars, funcs, glob = genCode(draw, localVars, localFuncs, globalfuntions, localProps)
        finalCode += code
        localVars = vars
        localFuncs = funcs
        globalfuntions = glob
        localProps["fuel"] -= 1

    return "for (%s in %s..%s) %s" % (varName, startValue, endValue, "{\n" + finalCode + "\n}\n"), variables, functions, globalfuntions

@composite
def genCallFunction(draw, variables, functions, globalfuntions):
    assume(len(functions) != 0 or len(globalfuntions) != 0)
    #if type == None:
    #    type = draw(genType())
    functionlist = functions.copy()
    for x in globalfuntions:
        functionlist.append((x[0], x[1], x[2]))
    #functionlist.extend([(f[0], f[1], f[2]) for f in globalfuntions])

    #functionlist = functions + globalfuntions
    #candidates = []
    #for cand in functionlist:
    #    if cand[1] == type:
    #        candidates.append(cand)
    # len(candidates) == o :(
    candidates = functionlist.copy()
    assume(len(candidates) != 0)
    function = draw(sampled_from(candidates))
    functionname = function[0]
    parameterlist = function[2]
    text = draw(names)
    code = "var " + text + " = null"
    #code = functionname + "(" + params + ")"
    return code, variables, functions, globalfuntions


@composite
def genExp(draw, variables, functions, globalfuntions, properties):
    return draw(one_of(
            genVariable(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genVariable(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genVariable(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genVariableChange(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genVariableChange(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genVariableChange(variables=variables, functions=functions, globalfuntions=globalfuntions),
            genFunction(variables=variables, functions=functions, globalfuntions=globalfuntions, properties=properties),
            genLoop(variables, functions, globalfuntions=globalfuntions, properties=properties)
        ))






variableAssignmentOperators = sampled_from(["=", "+=", "-=", "*="])  # Division (/ and %) is temporarily excluded
variableOperators = sampled_from(["+", "-", "*"])  # Division (/ and %) is temporarily excluded
stringAssignmentOperators = sampled_from(["=", "+="])


@composite
def chooseVariableName(draw, variables, varType=None, writeableRequired=True):
    if len(variables) == 0:
        #assume(varType != None)
        return str(draw(buildPrimitive(varType)))
    potentials = []
    for var in variables:
        if type(varType) in [list, tuple]:
            for values in varType:
                if var[1] == values and ((var[2] and writeableRequired) or not writeableRequired):
                    potentials.append(var[0])
        else:
            if (var[1] == varType or varType is None) and ((var[2] and writeableRequired) or not writeableRequired):
                potentials.append(var[0])
    if potentials == []:
        return str(draw(buildPrimitive(varType)))
    return draw(sampled_from(potentials))


@composite
def chooseVariable(draw, variables, varType=None, writeableRequired=True):
    assume(len(variables) != 0)
    potentials = []
    for var in variables:
        if type(varType) in [list, tuple]:
            for values in varType:
                if var[1] == values and ((var[2] and writeableRequired) or not writeableRequired):
                    potentials.append(var)
        else:
            if (var[1] == varType or varType is None) and ((var[2] and writeableRequired) or not writeableRequired):
                potentials.append(var)
    assume(len(potentials) != 0)
    return draw(sampled_from(potentials))


@composite
def buildValue(draw, variables, varType):
    if type(varType) not in [tuple, list]:
        varType = [varType]

    if any(x in varType for x in NUMBER_TYPES):
        operator = draw(variableOperators)
    elif "String" in varType:
        operator = "+"
    else:
        return draw(genValue(variables, varType))

    #if type in [list, tuple]:
    return draw(genValue(variables, varType)) + " " + operator + " " + draw(genValue(variables, varType))
    #else:
    #    return draw(genValue(variables, type)) + " " + operator + " " + draw(genValue(variables, COMPATIBLE_TYPES[type]))


@composite
def buildValueParenthesis(draw, variables, type):
    return "(" + draw(buildValue(variables, type)) + ")"


@composite
def buildPrimitive(draw, varType):
    if type(varType) not in [tuple, list]:
        varType = [varType]
    potentialStrategies = []

    if "Long" in varType:
        potentialStrategies.append(long)

    if "Int" in varType:
        potentialStrategies.append(integer)

    if "Double" in varType:
        potentialStrategies.append(just(float(draw(double))))

    if "String" in varType:
        potentialStrategies.append(just("\"" + draw(names) + "\""))

    return draw(one_of(potentialStrategies))


@composite
def genValue(draw, variables, type):
    return str(draw(one_of(
        buildPrimitive(type),
        buildValue(variables, type),
        buildValueParenthesis(variables, type),
        chooseVariableName(variables, type, writeableRequired=False)
    )))


@composite
def genType(draw):
    return draw(sampled_from(NUMBER_TYPES + ["String"]))


@composite
def genVariableChange(draw, variables, functions, globalfuntions):
    if len(variables) == 0:
        return draw(genVariable(variables, functions, globalfuntions))

    variable = draw(chooseVariable(variables))
    variableName = variable[0]
    type = variable[1]

    if type in NUMBER_TYPES:
        operator = draw(variableAssignmentOperators)
    elif type == "String":
        operator = draw(stringAssignmentOperators)
    else:
        operator = "="
    return (variableName + operator + str(
        draw(genValue(variables, type))) + ";\n"), variables, functions, globalfuntions


@composite
def genVariable(draw, variables, functions, globalfuntions, type=None):
    if type == None:
        type = draw(genType())
    value = draw(genValue(variables, type))
    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    name = draw(names.filter(lambda x: x not in variableNames))

    variables.append((name, type, True))
    return ('var ' + name + ': ' + type + ' = ' + str(value) + ';\n'), variables, functions, globalfuntions


@composite
def genF(draw, variables, functions, globalfuntions, properties):
    functionNames = []
    for funcName in functions:
        functionNames.append(funcName[0])
    name = draw(names.filter(lambda x: x not in functionNames))
    type = draw(genType())
    parameters, parametercode = draw(genParameters())
    localProps = properties.copy()
    localProps["fuel"] = draw(integers(min_value=1, max_value=min([30, properties["fuel"]])))
    properties["fuel"] -= localProps["fuel"]

    code = """\nfun """ + name + """(""" + parametercode + """ ) :""" + type + """? {
    input
    output
    }"""
    parameterlisttype = []
    for param in parameters:
        parameterlisttype.append(param[1])

    gen, parameters, extraFuncs, globalfuntions = genCode(draw, parameters, functions, globalfuntions, localProps)
    parameters += variables.copy()
    if len(parameters) == 0:
        returnvariable = None
    else:
        returnvariable = draw(chooseVariableName(parameters, type))
    if returnvariable is None:
        returncode = """return null"""
    else:
        returncode = """return """ + returnvariable
    functioncode = code.replace("input", gen).replace("output", returncode)
    return functioncode, name, type, variables, parameterlisttype, functions, globalfuntions

@composite
def genInLineFunction(draw, variables, functions, globalfuntions, properties):
    functioncode, functionname, funtiontype, variables, parameterlisttype, inlinefunction, globalfuntions = draw(genF(variables, functions, globalfuntions, properties))
    functions.append((functionname, funtiontype, parameterlisttype))
    return functioncode, variables, inlinefunction, globalfuntions

@composite
def genOutSideFunction(draw, variables, functions, globalfuntions, properties):
    functioncode, functionname, funtiontype, variables, parameterlisttype, inlinefunction, globalfuntions = draw(genF(variables, [], globalfuntions, properties))
    globalfuntions.append((functionname, funtiontype, parameterlisttype, functioncode))
    return "", variables, functions, globalfuntions

@composite
def genFunction(draw, variables, functions, globalfuntions, properties):
    return draw(one_of(
        genInLineFunction(variables=variables, functions=functions, globalfuntions=globalfuntions, properties=properties),
        genOutSideFunction(variables=variables, functions=functions, globalfuntions=globalfuntions, properties=properties)
    ))

@composite
def genParameters(draw):
    amount = draw(functionParametersCount)
    s = ""
    paramterlist = []
    paramternamelist = []
    for x in range(amount):
        type = draw(genType())
        name = draw(names.filter(lambda x: x not in paramternamelist))
        paramternamelist.append(name)
        paramterlist.append((name, type, False))
        s += name + " :" + type
        if x != amount - 1:
            s += ", "
    return paramterlist, s


@composite
def projectsv2(draw):
    fuel = draw(fuelGen)
    functions = []
    variables = []
    globalfuntions = []
    properties = {"fuel": fuel}
    gen, variables, functions, globalfuntions = genCode(draw, variables, functions, globalfuntions, properties)
    functioncode = ""
    for f in globalfuntions:
        functioncode += f[3]

    code = """fun main(args: Array<String>) {
input
}
externalsmegaawesomefunctions
    """

    return code.replace("input", gen).replace("externalsmegaawesomefunctions", functioncode)


def nativeRemover(inputString):
    inputString = inputString.replace("inline", "")
    inputString = inputString.replace("@TypedIntrinsic ", "")
    inputString = inputString.replace("external", "")
    return inputString.replace("-native", "")


@given(projectsv2())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=20,
          verbosity=Verbosity.debug)
def test_compilertest(s):
    milisec = TimestampMillisec64()
    name = "out/folder" + (str(milisec))
    print("run " + str(milisec))
    (output1) = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    (output2) = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert isEqual(output1, output2)


def isEqual(output1, output2):
    if str.__contains__(str(output1), "OutOfMemory") or str.__contains__(str(output2), "OutOfMemory"):
        return True

    if str.__contains__(str(output1), "cannot open output file") or str.__contains__(str(output2), "cannot open output file"):
        return True

    if str.__contains__(str(output1), "Division by zero") or str.__contains__(str(output2), "Division by zero"):
        return True

    assert nativeRemover(str(output1)) == nativeRemover(str(output2))
    return True


def TimestampMillisec64():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)


@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=5,
          verbosity=Verbosity.debug)
@given(names)
def simple_out(input):
    code = """fun main(args: Array<String>) {
println("{input}")
}""".replace("{input}", input)

    name = "out/folder" + (str(TimestampMillisec64()))
    output1 = runner.run(code, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(code, "kotlinc-native", outputDirectory=name + "-native")

    assert output1[1] == input + os.linesep
    assert output2[1] == input + os.linesep
