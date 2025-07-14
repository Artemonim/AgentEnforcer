import subprocess

class Plugin:
    language = 'kotlin'
    extensions = ['.kt', '.kts']

    def autofix_style(self, files):
        subprocess.run(['./gradlew', 'ktlintFormat'], check=False)

    def lint(self, files, disabled_rules):
        errors = []
        result = subprocess.run(['./gradlew', 'ktlintCheck'], capture_output=True, text=True)
        if result.stdout:
            errors.extend(result.stdout.splitlines())
        result = subprocess.run(['./gradlew', 'detekt'], capture_output=True, text=True)
        if result.stdout:
            errors.extend(result.stdout.splitlines())
        return errors

    def compile(self, files):
        result = subprocess.run(['./gradlew', 'assemble'], capture_output=True, text=True)
        return result.stdout.splitlines() if result.returncode != 0 else []

    def test(self, root_path):
        result = subprocess.run(['./gradlew', 'test'], capture_output=True, text=True)
        return result.stdout.splitlines() if result.returncode != 0 else []

    def get_required_commands(self):
        return ['./gradlew']  # Check for local wrapper 