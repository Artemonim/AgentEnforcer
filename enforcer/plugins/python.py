import subprocess
import json
import re
import sys

class Plugin:
    language = 'python'
    extensions = ['.py']

    def get_required_commands(self):
        return ['python']

    def autofix_style(self, files, tool_configs=None):
        tool_configs = tool_configs or {}
        changed_files = set()

        # Run black
        black_cmd = [sys.executable, '-m', 'black', '--quiet']
        if 'black' in tool_configs:
            black_cmd.extend(['--config', tool_configs['black']])
        black_cmd.extend(files)
        black_res = subprocess.run(black_cmd, capture_output=True, text=True, encoding='utf-8')
        if black_res.stderr:
            changed_files.update(re.findall(r"reformatted (.+)", black_res.stderr))

        # Run isort
        isort_cmd = [sys.executable, '-m', 'isort', '--quiet']
        if 'isort' in tool_configs:
            isort_cmd.extend(['--settings-path', tool_configs['isort']])
        isort_cmd.extend(files)
        isort_res = subprocess.run(isort_cmd, capture_output=True, text=True, encoding='utf-8')
        if isort_res.stderr:
            changed_files.update(re.findall(r"Fixing (.+)", isort_res.stderr))

        return {"changed_count": len(changed_files)}

    def lint(self, files, disabled_rules, tool_configs=None):
        tool_configs = tool_configs or {}
        errors = []
        warnings = []

        # Pyright
        pyright_cmd = [sys.executable, '-m', 'pyright', '--outputjson']
        pyright_cmd.extend(files)
        pyright_res = subprocess.run(pyright_cmd, capture_output=True, text=True, encoding='utf-8')
        if pyright_res.stdout:
            try:
                pyright_data = json.loads(pyright_res.stdout)
                for diag in pyright_data.get("generalDiagnostics", []):
                    issue = {
                        "tool": "pyright",
                        "file": diag.get("file"),
                        "line": diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                        "message": diag.get("message"),
                        "rule": diag.get("rule", "")
                    }
                    if diag.get('severity') == 'error':
                        errors.append(issue)
                    elif diag.get('severity') == 'warning':
                        warnings.append(issue)
            except json.JSONDecodeError:
                errors.append({"tool": "pyright", "file": "unknown", "line": 0, "message": "Failed to parse pyright JSON output"})

        # flake8
        flake8_cmd = [sys.executable, '-m', 'flake8', f'--ignore={",".join(disabled_rules)}']
        if 'flake8' in tool_configs:
            flake8_cmd.extend(['--config', tool_configs['flake8']])
        flake8_cmd.extend(files)
        flake8_res = subprocess.run(flake8_cmd, capture_output=True, text=True, encoding='utf-8')
        if flake8_res.stdout:
            for line in flake8_res.stdout.splitlines():
                match = re.match(r"([^:]+):(\d+):(\d+): ([EFWC]\d+) (.+)", line)
                if match:
                    code = match.group(4)
                    issue = {
                        "tool": "flake8", "file": match.group(1), "line": int(match.group(2)),
                        "message": match.group(5).strip(), "rule": code
                    }
                    if code.startswith('E') or code.startswith('F'):
                        errors.append(issue)
                    else:
                        warnings.append(issue)
        
        # mypy - all are errors
        mypy_cmd = [sys.executable, '-m', 'mypy']
        if 'mypy' in tool_configs:
            mypy_cmd.extend(['--config-file', tool_configs['mypy']])
        mypy_cmd.extend(files)
        mypy_res = subprocess.run(mypy_cmd, capture_output=True, text=True, encoding='utf-8')
        if mypy_res.stdout:
            for line in mypy_res.stdout.splitlines():
                match = re.match(r"([^:]+):(\d+): error: (.+)", line)
                if match:
                    message = match.group(3).strip()
                    rule_match = re.search(r"\[(.+)\]$", message)
                    rule = rule_match.group(1) if rule_match else ""
                    if rule_match:
                        message = message[:-len(rule_match.group(0))].strip()

                    errors.append({
                        "tool": "mypy", "file": match.group(1), "line": int(match.group(2)),
                        "message": message, "rule": rule
                    })

        return {"errors": errors, "warnings": warnings}

    def compile(self, files):
        errors = []
        for file in files:
            result = subprocess.run([sys.executable, '-m', 'py_compile', file], capture_output=True, text=True)
            if result.returncode != 0:
                errors.append(result.stderr)
        return errors

    def test(self, root_path):
        try:
            command = [sys.executable, '-m', 'pytest', root_path]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return []
        except subprocess.CalledProcessError as e:
            return [str(e.output)]
        except FileNotFoundError:
            return [] 