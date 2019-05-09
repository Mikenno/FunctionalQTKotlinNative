import glob
import os
import subprocess


def run(code, compiler="kotlinc", outputDirectory="out", codeFileName="code.kt", exeFileName=None) -> (bool, str):
    """
    Compiles the specified code and runs it.
    Returns a tuple containing the compiler output and the run output, in that order.

    Can use alternate compilers by specifying compiler=?

    Compilers available:
     - kotlinc
     - kotlinc-jvm
     - kotlinc-native (on windows and Linux)
     - kotlinc-experimental (on windows and Linux)

    :param code: the code to compile
    :param compiler: the compiler to use, defaults to kotlinc
    :param codeFileName: the name to save the code file in
    :param exeFileName: the name to save the exe file in
    :param outputDirectory: the working directory
    :return: a tuple containing the output (compiler, program)
    """
    if exeFileName == None:
        exeFileName = codeFileName.split(".")[0]

    prepareOutputDirectory(outputDirectory)

    codeFileName = outputDirectory + "/" + codeFileName
    exeFileName = outputDirectory + "/" + exeFileName

    checkPrerequisites(code, compiler)
    writeCodeFile(code, codeFileName)
    compilerOutput = compileFile(codeFileName, exeFileName, compiler)
    runOutput = runFile(exeFileName, compiler)
    return compilerOutput, runOutput


def runFile(file, compiler):
    if compiler == "kotlinc-jvm" or compiler == "kotlinc":
        file = file + ".jar"
    elif isWindows():
        file = file + ".exe"
    else:
        file = file + ".kexe"

    if os.path.exists(file):
        if compiler == "kotlinc-jvm" or compiler == "kotlinc":
            executionString = "java -jar " + file
        else:
            if isWindows():
                executionString = file.replace("/", "\\")
            else:
                executionString = "./" + file
        return subprocess.run(executionString, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True).stdout.decode('utf-8')
    return None


def isWindows():
    return os.name == "nt"


def compileFile(inputFile, outputFile, compiler):
    if compiler == "kotlinc-jvm" or compiler == "kotlinc":
        outputFile = outputFile + ".jar"
        executionString = "kotlinc/bin/{} {} -include-runtime -d {}".format(compiler, inputFile, outputFile)

        if os.name == 'nt':
            executionString = executionString.replace("/", "\\")

    elif compiler == "kotlinc-native":
        if isWindows():
            outputFile = outputFile.replace("/", "\\")
            inputFile = inputFile.replace("/", "\\")

            executionString = "kotlinc-windows\\bin\\{} -o {output} {input}".format(compiler, input=inputFile,
                                                                                    output=outputFile)
        else:
            outputFile = outputFile + ".kexe"
            executionString = "kotlinc-linux/bin/{} -o {output} {input}".format(compiler, input=inputFile,
                                                                                output=outputFile)
    elif compiler == "kotlinc-experimental":
        if isWindows():
            outputFile = outputFile.replace("/", "\\")
            inputFile = inputFile.replace("/", "\\")

            executionString = "kotlinc-experimental-windows\\bin\\kotlinc -o {output} {input}".format(input=inputFile,
                                                                                                      output=outputFile)
        else:
            outputFile = outputFile + ".kexe"
            executionString = "kotlinc-experimental-linux/bin/kotlinc -o {output} {input}".format(input=inputFile,
                                                                                                  output=outputFile)
    try:
        proc = subprocess.run(executionString.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False).stdout.decode(
        'utf-8')
    except subprocess.CalledProcessError as e:
        pass
    return proc


def checkPrerequisites(code, compiler):
    if compiler == "kotlinc-native":
        if os.name == "nt":
            if not os.path.exists("kotlinc-windows/bin/" + compiler):
                raise Exception(
                    "ERROR: Please include standalone native kotlin compiler in kotlinc-windows folder, aborting")
        else:
            if not os.path.exists("kotlinc-linux/bin/" + compiler):
                raise Exception(
                    "ERROR: Please include standalone native kotlin compiler in kotlinc-linux folder, aborting")
    elif compiler == "kotlinc-experimental":
        if os.name == "nt":
            if not os.path.exists("kotlinc-experimental-windows/bin/kotlinc"):
                raise Exception(
                    "ERROR: Please include standalone experimental native kotlin compiler in kotlinc-experimental-windows folder, aborting")
        else:
            if not os.path.exists("kotlinc-experimental-linux/bin/kotlinc"):
                raise Exception(
                    "ERROR: Please include standalone experimental native kotlin compiler in kotlinc-experimental-linux folder, aborting")
    else:
        if not os.path.exists("kotlinc/bin/" + compiler):
            raise Exception("ERROR: Please include standalone kotlin compiler in kotlinc folder, aborting")
    if code == "":
        print("Warning: Code is blank")


def writeCodeFile(code, outputFile):
    f = open(outputFile, "w")
    f.write(code)
    f.flush()
    f.close()


def prepareOutputDirectory(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)
    else:
        files = glob.glob(directory + '/*')
        for f in files:
            os.remove(f)
