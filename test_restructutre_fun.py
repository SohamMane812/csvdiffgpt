"""
Script to test the restructure function both programmatically and via CLI.
"""
import os
import subprocess
import json
from csvdiffgpt import restructure

def test_programmatically(csv_file="./baseball.csv"):
    """Test the restructure function programmatically."""
    print("=" * 70)
    print("TESTING RESTRUCTURE FUNCTION PROGRAMMATICALLY")
    print("=" * 70)
    
    generated_files = []
    
    # Test with all formats
    formats = ["sql", "mermaid", "python"]
    
    for format in formats:
        print(f"\nTesting with {format} format...")
        try:
            # Generate restructuring recommendations
            results = restructure(
                file=csv_file,
                format=format,
                use_llm=False
            )
            
            print(f"Generated {results['recommendation_count']} {format} recommendations")
            print("Recommendations by type:")
            for rec_type, count in results['recommendations_by_type'].items():
                print(f"  - {rec_type}: {count}")
            
            print("\nRecommendations by severity:")
            for severity, count in results['recommendations_by_severity'].items():
                print(f"  - {severity}: {count}")
            
            # Save code to file
            output_file = f"generated_{format}_restructure.{'py' if format == 'python' else format}"
            with open(output_file, 'w') as f:
                f.write(results["output_code"])
            print(f"Saved {format} code to {output_file}")
            
            generated_files.append(output_file)
            
        except Exception as e:
            print(f"Error testing {format}: {str(e)}")
    
    return generated_files

def test_via_cli(csv_file="./baseball.csv"):
    """Test the restructure function via CLI."""
    print("\n" + "=" * 70)
    print("TESTING RESTRUCTURE FUNCTION VIA CLI")
    print("=" * 70)
    
    generated_files = []
    
    # Test with all formats
    formats = ["sql", "mermaid", "python"]
    
    for format in formats:
        print(f"\nTesting with {format} format via CLI...")
        output_file = f"cli_{format}_restructure.{'py' if format == 'python' else format}"
        
        cmd = [
            "python", "-m", "csvdiffgpt.cli", 
            "restructure", csv_file, 
            "--no-llm", 
            "--format", format,
            "--output", output_file
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Success! CLI command generated {format} restructuring and saved to {output_file}")
                generated_files.append(output_file)
            else:
                print(f"Error running CLI command for {format}:")
                print(result.stderr)
        except Exception as e:
            print(f"Exception running CLI command for {format}: {str(e)}")
    
    return generated_files

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
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nGenerated files:")
    for file in programmatic_files + cli_files:
        if os.path.exists(file):
            print(f"- {file} ({os.path.getsize(file)} bytes)")

if __name__ == "__main__":
    main()