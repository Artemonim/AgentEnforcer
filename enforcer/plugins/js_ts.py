import subprocess

class Plugin:
    language = 'js_ts'
    extensions = ['.js', '.ts', '.jsx', '.tsx']

    def autofix_style(self, files):
        for file in files:
            subprocess.run(['npx', 'prettier', '--write', file], check=False)

    def lint(self, files, disabled_rules):
        errors = []
        for file in files:
            result = subprocess.run(['npx', 'eslint', file], capture_output=True, text=True)
            if result.stdout:
                errors.extend(result.stdout.splitlines())
        return errors

    def compile(self, files):
        # Run tsc on the project
        result = subprocess.run(['npx', 'tsc'], capture_output=True, text=True)  # Assumes tsconfig.json
        return result.stdout.splitlines() if result.returncode != 0 else []

    def test(self, root_path):
        try:
            result = subprocess.run(['npx', 'jest', root_path], check=True, capture_output=True, text=True)
            return []
        except subprocess.CalledProcessError as e:
            return e.output.splitlines()
        except FileNotFoundError:
            return []  # No tests 

    def get_required_commands(self):
        return ['npx', 'prettier', 'eslint', 'tsc', 'jest'] 