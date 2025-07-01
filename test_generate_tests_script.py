"""
Robust script to test the generate_tests function both programmatically and via CLI.
"""
import os
import subprocess
import json
import sys
from csvdiffgpt import generate_tests

def test_programmatically(csv_file="./baseball.csv"):
    """Test the generate_tests function programmatically."""
    print("=" * 70)
    print("TESTING GENERATE_TESTS FUNCTION PROGRAMMATICALLY")
    print("=" * 70)
    
    generated_files = []
    
    # Test with all frameworks
    frameworks = ["pytest", "great_expectations", "dbt"]
    
    for framework in frameworks:
        print(f"\nTesting with {framework} framework...")
        try:
            # Generate tests
            results = generate_tests(
                file=csv_file,
                framework=framework,
                model_name="baseball" if framework == "dbt" else None,
                use_llm=False
            )
            
            print(f"Generated {results['test_count']} {framework} tests")
            print("Tests by type:")
            for test_type, count in results['tests_by_type'].items():
                print(f"  - {test_type}: {count}")
            
            print("\nTests by severity:")
            for severity, count in results['tests_by_severity'].items():
                print(f"  - {severity}: {count}")
            
            # Save code to file
            output_file = f"generated_{framework.replace('_', '')}_tests.{'py' if framework != 'dbt' else 'yml'}"
            with open(output_file, 'w') as f:
                f.write(results["test_code"])
            print(f"Saved {framework} code to {output_file}")
            
            generated_files.append(output_file)
            
        except Exception as e:
            print(f"Error testing {framework}: {str(e)}")
    
    return generated_files

def test_via_cli(csv_file="./baseball.csv"):
    """Test the generate_tests function via CLI."""
    print("\n" + "=" * 70)
    print("TESTING GENERATE_TESTS FUNCTION VIA CLI")
    print("=" * 70)
    
    generated_files = []
    
    # Test with all frameworks
    frameworks = ["pytest", "great_expectations", "dbt"]
    
    for framework in frameworks:
        print(f"\nTesting with {framework} framework via CLI...")
        output_file = f"cli_{framework.replace('_', '')}_tests.{'py' if framework != 'dbt' else 'yml'}"
        
        cmd = [
            sys.executable, "-m", "csvdiffgpt.cli", 
            "generate-tests", csv_file, 
            "--no-llm", 
            "--framework", framework
        ]
        
        # Add model-name for dbt
        if framework == "dbt":
            cmd.extend(["--model-name", "baseball"])
        
        # Add output file
        cmd.extend(["--output", output_file])
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Success! CLI command generated {framework} tests and saved to {output_file}")
                generated_files.append(output_file)
            else:
                print(f"Error running CLI command for {framework}:")
                print(result.stderr)
        except Exception as e:
            print(f"Exception running CLI command for {framework}: {str(e)}")
    
    return generated_files

def test_running_generated_tests(pytest_file="generated_pytest_tests.py", csv_file="./baseball.csv"):
    """Test running the generated pytest tests."""
    if not os.path.exists(pytest_file):
        print(f"Cannot run tests: {pytest_file} not found")
        return
        
    print("\n" + "=" * 70)
    print("TESTING RUNNING THE GENERATED PYTEST TESTS")
    print("=" * 70)
    
    # Copy the CSV file to the same directory as the test file
    csv_basename = os.path.basename(csv_file)
    if not os.path.exists(csv_basename):
        print(f"Copying {csv_file} to current directory for pytest to find it...")
        try:
            with open(csv_file, 'rb') as src, open(csv_basename, 'wb') as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"Error copying file: {str(e)}")
            return
    
    # Run pytest on the generated file
    print(f"\nRunning: pytest {pytest_file} -v")
    try:
        result = subprocess.run(["pytest", pytest_file, "-v"], capture_output=True, text=True)
        
        print("\nTest Results:")
        if result.returncode == 0:
            print("All tests passed!")
        else:
            print("Some tests failed")
        
        print("\nTest Output Summary:")
        # Print just the summary part of pytest output
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) > 5:
            for line in output_lines[-5:]:
                print(line)
        else:
            print(result.stdout)
            
        print(f"\nFull test output saved to pytest_results.txt")
        with open("pytest_results.txt", "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)
                
    except Exception as e:
        print(f"Error running pytest: {str(e)}")

def main():
    """Run all tests."""
    # CSV file to test with
    csv_file = "./baseball.csv"
    
    # Ensure the CSV file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found at {csv_file}")
        print("Please provide a valid path to a CSV file")
        return
    
    # Test programmatically
    programmatic_files = test_programmatically(csv_file)
    
    # Test via CLI
    cli_files = test_via_cli(csv_file)
    
    # Test running the generated pytest tests
    if programmatic_files and os.path.exists(programmatic_files[0]):
        test_running_generated_tests(programmatic_files[0], csv_file)
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nGenerated files:")
    for file in programmatic_files + cli_files:
        if os.path.exists(file):
            print(f"- {file} ({os.path.getsize(file)} bytes)")

if __name__ == "__main__":
    main()