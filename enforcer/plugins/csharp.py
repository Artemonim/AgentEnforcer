import subprocess
import re

class Plugin:
    language = 'csharp'
    extensions = ['.cs']

    def get_required_commands(self):
        return ['dotnet']

    def autofix_style(self, files, tool_configs=None):
        subprocess.run(['dotnet', 'format'], check=False, capture_output=True)
        return {"changed_count": 0} # dotnet format doesn't reliably report changes

    def lint(self, files, disabled_rules, tool_configs=None):
        # In C#, linting and compilation are often the same step.
        # We run build here and parse errors/warnings.
        return self._run_build()

    def compile(self, files):
        # This step is combined with lint for C# projects.
        # Returning no errors as build is handled in lint().
        return []

    def test(self, root_path):
        result = subprocess.run(['dotnet', 'test'], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return [{"tool": "dotnet-test", "message": result.stdout or result.stderr}]
        return []
    
    def _run_build(self):
        errors = []
        warnings = []
        # This regex captures the standard format of dotnet build errors/warnings
        # Example: C:\Path\File.cs(10,5): error CS0103: The name 'xyz' does not exist...
        pattern = re.compile(r"(.+)\((\d+),(\d+)\):\s+(warning|error)\s+([A-Z0-9]+):\s+(.+)")
        
        result = subprocess.run(['dotnet', 'build'], capture_output=True, text=True, encoding='utf-8')
        output = result.stdout + result.stderr

        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                issue = {
                    "tool": "dotnet-build",
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "message": match.group(6).strip(),
                    "rule": match.group(5)
                }
                if match.group(4) == 'error':
                    errors.append(issue)
                else:
                    warnings.append(issue)
        
        return {"errors": errors, "warnings": warnings} 