import subprocess
import re

class Plugin:
    language = 'kotlin'
    extensions = ['.kt', '.kts']

    def get_required_commands(self):
        return ['./gradlew']

    def autofix_style(self, files, tool_configs=None):
        subprocess.run(['./gradlew', 'ktlintFormat', '--quiet'], check=False, capture_output=True)
        return {"changed_count": 0} # Can't easily tell, assume 0 for now

    def lint(self, files, disabled_rules, tool_configs=None):
        warnings = []

        # ktlint - all issues are warnings by default
        ktlint_result = subprocess.run(['./gradlew', 'ktlintCheck'], capture_output=True, text=True, encoding='utf-8')
        # Example: /path/to/File.kt:10:5: Unused import
        ktlint_pattern = re.compile(r"(.+):(\d+):(\d+):\s+(.+)")
        if ktlint_result.stdout:
            for line in ktlint_result.stdout.splitlines():
                match = ktlint_pattern.match(line)
                if match:
                    warnings.append({
                        "tool": "ktlint", "file": match.group(1), "line": int(match.group(2)),
                        "message": match.group(4).strip()
                    })

        # detekt - all issues are warnings
        detekt_result = subprocess.run(['./gradlew', 'detekt'], capture_output=True, text=True, encoding='utf-8')
        # Example: /path/to/File.kt:10:5 - SomeRule - Some issue
        detekt_pattern = re.compile(r"(.+):(\d+):(\d+)\s+-\s+(.+)\s+-\s+(.+)")
        if detekt_result.stdout:
            for line in detekt_result.stdout.splitlines():
                 match = detekt_pattern.match(line)
                 if match:
                     warnings.append({
                        "tool": "detekt", "file": match.group(1), "line": int(match.group(2)),
                        "message": match.group(5).strip(), "rule": match.group(4).strip()
                    })
        
        return {"errors": [], "warnings": warnings}

    def compile(self, files):
        result = subprocess.run(['./gradlew', 'assemble'], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            # Treat as a single error for now
            return [{"tool": "gradle-assemble", "message": "Build failed. See logs for details."}]
        return []

    def test(self, root_path):
        result = subprocess.run(['./gradlew', 'test'], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return [{"tool": "gradle-test", "message": "Tests failed. See logs for details."}]
        return [] 