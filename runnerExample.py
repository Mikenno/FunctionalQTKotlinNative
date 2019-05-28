import runner

code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }"""
output = runner.run(code,outputDirectory="out/example")

print(output[0])

output = runner.run(code, "kotlinc-native", outputDirectory="out/example")

print(output[0])