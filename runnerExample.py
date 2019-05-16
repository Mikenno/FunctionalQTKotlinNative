import runner

code = """fun main(args: Array<String>) {\n\tvar AAA = 0;\n\tvar AAB = 0;\n\tvar ABB = 0;\n\tvar BAA = 0;\n\tvar ABA = 0;\n\tvar AAAA = AAA;\n\tvar BBA = A
AA;\n\tBBA=0;\n\tBAA=0;\n\tBBA=0;\n\tBAA=0;\n\tAAA=0;\n\tABB=0;\n\tABA=0;\n\tBAA=0;\n\tBAA=0;\n\tBBA=0;\n\tBBA=0;\n\tABB=0;\n\tBAA=0;\n\tABB=0;\n\tABA=0;\n\tAAB=AAA;\n\tABA=AAA;\n\tAAB=A
AA;\n}\n    """
output = runner.run(code,outputDirectory="out\\example")

print(output[0])

output = runner.run(code, "kotlinc-native", outputDirectory="out\\example")

print(output[0])