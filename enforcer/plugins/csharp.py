import subprocess

class Plugin:
    language = 'csharp'
    extensions = ['.cs']

    def autofix_style(self, files):
        subprocess.run(['dotnet', 'format'], check=False)  # Assumes in project dir

    def lint(self, files, disabled_rules):
        # For C#, lint might be part of build or separate tool like StyleCop
        # For now, skip or use roslyn analyzers in build
        return []

    def compile(self, files):
        result = subprocess.run(['dotnet', 'build'], capture_output=True, text=True)
        return result.stderr.splitlines() if result.returncode != 0 else []

    def test(self, root_path):
        result = subprocess.run(['dotnet', 'test'], capture_output=True, text=True)
        return result.stderr.splitlines() if result.returncode != 0 else []

    def get_required_commands(self):
        return ['dotnet'] 