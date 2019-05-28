import pytest
from hypothesis._strategies import randoms, sampled_from, one_of, recursive, builds, data

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

ARRAY_STR_ID = "Array<String>"

NUMBER_TYPES = ["Long", "Int", "Double"]
COMPATIBLE_TYPES = {"String": ["String"] + NUMBER_TYPES,
                    "Long": NUMBER_TYPES,
                    "Int": NUMBER_TYPES,
                    "Double": NUMBER_TYPES}

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=4)

long = integers(min_value=-math.pow(2, 63), max_value=(math.pow(2, 63) - 1))
integer = integers(min_value=-math.pow(2, 31), max_value=math.pow(2, 31) - 1)
positiveInteger = integers(min_value=0, max_value=math.pow(2, 63) - 1)
negativeInteger = integers(min_value=-math.pow(2, 63), max_value=0)
double = decimals(allow_infinity=False, allow_nan=False)

functionParametersCount = integers(min_value=0, max_value=10)
fuelGen = integers(min_value=10, max_value=500)


@composite
def projects(draw):
    name = draw(names)
    code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }
    """
    return code.replace("World", name)

@composite
def genCode(draw, variables, functions, globalfunctions, properties):
    string_code = ""
    while properties["fuel"] > 0:
        newCode, newVariableList, functions, globalfunctions = draw(
            genExp(variables, functions, globalfunctions, properties))
        variables = newVariableList
        string_code += newCode
        properties["fuel"] -= 1
    return string_code, variables, functions, globalfunctions


@composite
def genLoop(draw, variables, functions, globalfunctions, properties):
    startValue = draw(integers(max_value=math.pow(2, 8), min_value=-math.pow(2, 8)))

    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    varName = draw(names.filter(lambda x: x not in variableNames))
    endValue = draw(integers(max_value=math.pow(2, 8), min_value=-math.pow(2, 8)))

    localProps = properties.copy()
    localProps["fuel"] = draw(integers(min_value=1, max_value=min([20, properties["fuel"]])))
    localProps["depth"] = localProps["depth"] + 1
    properties["fuel"] -= localProps["fuel"]
    finalCode = ""

    localVars = variables.copy()
    localVars += [(varName, "Int", False)]
    localFuncs = functions.copy()

    while localProps["fuel"] > 0:
        code, vars, funcs, glob = draw(genCode(localVars, localFuncs, globalfunctions, localProps))
        finalCode += code
        localVars = vars
        localFuncs = funcs
        globalfunctions = glob
        localProps["fuel"] -= 1

    indentation = properties["depth"] * "    "
    return indentation + "for (%s in %s..%s) %s" % (varName, startValue, endValue,
                                                    "{\n" + finalCode + "\n" + indentation + "}\n"), variables, functions, globalfunctions


@composite
def buildCallFunction(draw, variables, functions, globalfunctions, properties, type=None):
    return draw(genCallFunction(variables, functions, globalfunctions, properties, type))[0]

@composite
def genCallFunction(draw, variables, functions, globalfunctions, properties, type=None):
    functionlist = functions.copy()
    for x in globalfunctions:
        functionlist.append((x[0], x[1], x[2]))
    # functionlist.extend([(f[0], f[1], f[2]) for f in globalfunctions])
    candidates = []
    if type != None:
        for cand in functionlist:
            if cand[1] == type:
                candidates.append(cand)
    else:
        candidates = functionlist.copy()
    if candidates == []:
        return [str(draw(buildPrimitive(type))), variables, functions, globalfunctions]
    function = draw(sampled_from(candidates))
    functionname = function[0]
    parameterlist = function[2]
    paramcode = ""
    for param in parameterlist:
        paramcode += draw(chooseVariableName(variables, param, False)) + ", "
    paramcode = paramcode[:-2]
    code = functionname + "(" + paramcode + ")" + "\n"
    return code, variables, functions, globalfunctions


@composite
def genExp(draw, variables, functions, globalfunctions, properties):
    expressionGens = [
        genVariable(variables=variables, functions=functions, globalfunctions=globalfunctions, properties=properties),
        genVariable(variables=variables, functions=functions, globalfunctions=globalfunctions, properties=properties),
        genVariable(variables=variables, functions=functions, globalfunctions=globalfunctions, properties=properties),
        genVariableChange(variables=variables, functions=functions, globalfunctions=globalfunctions,
                          properties=properties),
        genVariableChange(variables=variables, functions=functions, globalfunctions=globalfunctions,
                          properties=properties),
        genVariableChange(variables=variables, functions=functions, globalfunctions=globalfunctions,
                          properties=properties),
        genFunction(variables=variables, functions=functions, globalfunctions=globalfunctions,
                    properties=properties),
        genFunction(variables=variables, functions=functions, globalfunctions=globalfunctions,
                    properties=properties),
        genFunction(variables=variables, functions=functions, globalfunctions=globalfunctions,
                    properties=properties),
        genLoop(variables, functions, globalfunctions=globalfunctions, properties=properties)]

    if len(functions) != 0 or len(globalfunctions) != 0:
        expressionGens.append(genCallFunction(variables, functions, globalfunctions, properties=properties))
        expressionGens.append(genCallFunction(variables, functions, globalfunctions, properties=properties))

    return draw(one_of(expressionGens))


variableAssignmentOperators = sampled_from(["=", "+=", "-=", "*="])  # Division (/ and %) is temporarily excluded
variableOperators = sampled_from(["+", "-", "*"])  # Division (/ and %) is temporarily excluded
stringAssignmentOperators = sampled_from(["=", "+="])


@composite
def chooseVariableName(draw, variables, varType=None, writeableRequired=True):
    if len(variables) == 0:
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
def buildArray(draw, variables, functions, globalfunctions, properties):
    localprop = properties.copy()
    localprop["fuel"] = draw(integers(min_value=1, max_value=20))
    stringCode = ""
    startFuel = localprop["fuel"]
    for fuel in range(localprop["fuel"]):
        stringCode += str(draw(genValue(variables, functions, globalfunctions, "String", properties)))
        if (fuel != startFuel - 1):
            stringCode += ", "
        localprop["fuel"] -= 1

    return "arrayOf(" + str(stringCode) + ")"


@composite
def buildValue(draw, variables, functions, globalfunctions, varType, properties):
    if type(varType) not in [tuple, list]:
        varType = [varType]

    if any(x in varType for x in NUMBER_TYPES):
        operator = draw(variableOperators)
    elif "String" in varType:
        operator = "+"
    else:
        return draw(genValue(variables, functions, globalfunctions, varType, properties))

    # if type in [list, tuple]:
    return draw(genValue(variables, functions, globalfunctions, varType, properties)) + " " + operator + " " + draw(
        genValue(variables, functions, globalfunctions, varType, properties))
    # else:
    #    return draw(genValue(variables, type)) + " " + operator + " " + draw(genValue(variables, COMPATIBLE_TYPES[type]))


@composite
def buildValueParenthesis(draw, variables, functions, globalfunctions, type, properties):
    return "(" + draw(buildValue(variables, functions, globalfunctions, type, properties)) + ")"


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

    if ARRAY_STR_ID in varType:
        potentialStrategies.append(just("arrayOf<String>()"))

    return draw(one_of(potentialStrategies))


@composite
def genValue(draw, variables, functions, globalfunctions, type, properties):
    if (type == ARRAY_STR_ID):
        init = str(draw(buildArray(variables, functions, globalfunctions, properties)))
        return init
    else:
        return str(draw(one_of(
            buildPrimitive(type),
            buildValue(variables, functions, globalfunctions, type, properties),
            buildValueParenthesis(variables, functions, globalfunctions, type, properties),
            chooseVariableName(variables, type, writeableRequired=False),
            buildCallFunction(variables, functions, globalfunctions, properties, type)
        )))


@composite
def genType(draw):
    return draw(sampled_from(NUMBER_TYPES + ["String", ARRAY_STR_ID]))  # ONE DOES NOT SIMPLY ADD ARRAY_STR_ID!


@composite
def genVariableChange(draw, variables, functions, properties, globalfunctions):
    if len(variables) == 0:
        return draw(genVariable(variables, functions, properties, globalfunctions=globalfunctions))

    variable = draw(chooseVariable(variables))
    variableName = variable[0]
    type = variable[1]

    if type in NUMBER_TYPES:
        operator = draw(variableAssignmentOperators)
    elif type == "String":
        operator = draw(stringAssignmentOperators)
    else:
        operator = "="

    indentation = properties["depth"] * "    "
    return indentation + (variableName + operator + str(
        draw(genValue(variables, functions, globalfunctions, type, properties))) + ";\n"), variables, functions, globalfunctions


@composite
def genVariable(draw, variables, functions, properties, globalfunctions, type=None):
    if type == None:
        type = draw(genType())
    value = draw(genValue(variables, functions, globalfunctions, type, properties))
    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    name = draw(names.filter(lambda x: x not in variableNames))

    variables.append((name, type, True))
    indentation = properties["depth"] * "    "
    return indentation + (
            'var ' + name + ': ' + type + ' = ' + str(value) + ';\n'), variables, functions, globalfunctions


@composite
def genF(draw, variables, functions, globalfunctions, properties):
    functionNames = []
    for funcName in functions:
        functionNames.append(funcName[0])
    name = draw(names.filter(lambda x: x not in functionNames))
    type = draw(genType())
    parameters, parametercode = draw(genParameters())
    localProps = properties.copy()
    localProps["fuel"] = draw(integers(min_value=1, max_value=min([30, properties["fuel"]])))
    properties["fuel"] -= localProps["fuel"]

    localFuncs = functions.copy()

    localProps["depth"] += 1
    indentation = properties["depth"] * "    "
    code = indentation + """fun """ + name + """(""" + parametercode + """ ) :""" + type + """ {
input
output
""" + indentation + "}\n"
    parameterlisttype = []
    for param in parameters:
        parameterlisttype.append(param[1])

    parameters += variables.copy()
    gen, parameters, extraFuncs, globalfunctions = draw(genCode(parameters, localFuncs, globalfunctions, localProps))
    if len(parameters) == 0:
        returnvariable = draw(buildPrimitive(type))
    else:
        returnvariable = draw(chooseVariableName(parameters, type))

    returncode = """return """ + str(returnvariable)
    returncode = indentation + returncode
    functioncode = code.replace("input", gen).replace("output", returncode)
    return functioncode, name, type, variables, parameterlisttype, functions, globalfunctions


@composite
def genInLineFunction(draw, variables, functions, globalfunctions, properties):
    functioncode, functionname, funtiontype, variables, parameterlisttype, inlinefunction, globalfunctions = draw(
        genF(variables, functions, globalfunctions, properties))
    functions.append((functionname, funtiontype, parameterlisttype))
    return functioncode, variables, inlinefunction, globalfunctions


@composite
def genOutSideFunction(draw, variables, functions, globalfunctions, properties):
    localProps = properties.copy()
    localProps["depth"] = 0
    functioncode, functionname, funtiontype, _, parameterlisttype, inlinefunction, globalfunctions = draw(
        genF([], [], globalfunctions, localProps))
    globalfunctions.append((functionname, funtiontype, parameterlisttype, functioncode))
    return "", variables, functions, globalfunctions


@composite
def genFunction(draw, variables, functions, globalfunctions, properties):
    return draw(one_of(
        genInLineFunction(variables=variables, functions=functions, globalfunctions=globalfunctions,
                          properties=properties),
        genOutSideFunction(variables=variables, functions=functions, globalfunctions=globalfunctions,
                           properties=properties)
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
def projectsv2(draw, functions=None, variables=None, properties=None):
    if properties is None:
        fuel = draw(fuelGen)
        properties = {"fuel": fuel, "depth": 1}
    if variables is None:
        variables = []
    if functions is None:
        functions = []
    globalfunctions = []
    gen, variables, functions, globalfunctions = draw(genCode(variables, functions, globalfunctions, properties))
    functioncode = ""
    for f in globalfunctions:
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

@given(data())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=5,
          verbosity=Verbosity.debug)
def test_dead_code(data):
    variables = [("variable1", "String", False)]
    fuel = data.draw(fuelGen)
    gen, _, _, globalFuncs = data.draw(genCode(variables, [], [], {"fuel": fuel, "depth":1}))
    functioncode = ""
    for f in globalFuncs:
        functioncode += f[3]

    input = data.draw(names)
    code = """fun main(args: Array<String>) {
    var variable1 = "%s"
%s
    print(variable1)
}
%s""" % (input, gen, functioncode)

    name = "out/folder" + (str(TimestampMillisec64()))
    output1 = runner.run(code, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(code, "kotlinc-native", outputDirectory=name + "-native")

    assert output1[1] == input
    assert output2[1] == input

@given(projectsv2())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=50,
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

    if str.__contains__(str(output1), "cannot open output file") or str.__contains__(str(output2),
                                                                                     "cannot open output file"):
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
def test_simple_out(input):
    code = """fun main(args: Array<String>) {
println("{input}")
}""".replace("{input}", input)

    name = "out/folder" + (str(TimestampMillisec64()))
    output1 = runner.run(code, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(code, "kotlinc-native", outputDirectory=name + "-native")

    assert output1[1] == input + os.linesep
    assert output2[1] == input + os.linesep

@given(data())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=5,
          verbosity=Verbosity.debug)
@pytest.mark.xfail()
def test_error_on_different_output(data):
    fuel = data.draw(fuelGen)
    properties = {"fuel": fuel, "depth": 1}
    gen, variables, functions, globalfunctions = data.draw(genCode([], [], [], properties))
    functioncode = ""
    for f in globalfunctions:
        functioncode += f[3]

    code = """fun main(args: Array<String>) {
    input
    }
    externalsmegaawesomefunctions
        """

    code = code.replace("input", gen).replace("externalsmegaawesomefunctions", functioncode)

    name = "out/folder" + (str(TimestampMillisec64()))
    output1 = runner.run(code, "kotlinc-jvm", outputDirectory=name)

    code = """fun main(args: Array<String>) {
    println("Hello failing test")
}
"""
    output2 = runner.run(code, "kotlinc-native", outputDirectory=name + "-native")

    assert isEqual(output1, output2)