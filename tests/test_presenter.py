from enforcer.presenter import Presenter
def test_status():
    p = Presenter()
    p.status("test msg", "warning")
    assert "[!] test msg" in p.get_output()
def test_separator():
    p = Presenter()
    p.separator("Test")
    assert "--- Test ---" in p.get_output()
def test_display_results():
    p = Presenter()
    errors = [{"file": "f.py", "line": 1, "col": 2, "rule": "E1", "message": "err"}]
    warnings = [{"file": "f.py", "line": 3, "col": 4, "rule": "W1", "message": "warn"}]
    final_errors, final_warnings = p.display_results(errors, warnings, "python", {"E1": "error"})
    output = p.get_output()
    assert "Errors:" in output
    assert "- [ERROR] f.py:1:2 err (E1)" in output
    assert "Warnings:" in output
    assert "- [WARNING] f.py:3:4 warn (W1)" in output
def test_final_summary():
    p = Presenter()
    p.final_summary([{"message": "err"}], [{"message": "warn"}, {"message": "warn2"}])
    output = p.get_output()
    assert "Total Errors: 1" in output
    assert "Total Warnings: 2" in output
    assert "! Check failed with errors." in output 
def test_final_summary_with_many_errors():
    p = Presenter()
    errors = [{"file": f"f{i}.py", "message": "err"} for i in range(11)]
    p.final_summary(errors, [])
    output = p.get_output()
    assert "Total Errors: 11" in output
    assert "Top 3 files with most errors:" in output
def test_print_grouped_summary():
    p = Presenter()
    issues = [{"file": "f1.py", "tool": "tool1", "rule": "R1", "line": 1}, {"file": "f1.py", "tool": "tool1", "rule": "R1", "line": 2}]
    p._print_grouped_summary(issues)
    output = p.get_output()
    assert "f1.py (2 issues)" in output
    assert "[tool1][R1] at lines 1, 2" in output 