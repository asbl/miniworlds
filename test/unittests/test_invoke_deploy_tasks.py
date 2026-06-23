from types import SimpleNamespace

import pytest

import tasks


pytestmark = pytest.mark.unit


class DummyContext:
    pass


def _patch_branches(monkeypatch):
    def current_branch(c, repo_path, name):
        return "main" if name == "Main" else "physics-main"

    monkeypatch.setattr(tasks, "_current_branch", current_branch)


def test_deploy_push_runs_tests_before_pushing(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "tests_run", lambda c: events.append("tests"))
    monkeypatch.setattr(
        tasks,
        "_push_repositories",
        lambda c, main_branch, physics_branch, tags: events.append(
            ("push", main_branch, physics_branch, tags)
        ),
    )

    tasks.deploy_push.body(DummyContext(), tags=True)

    assert events == ["tests", ("push", "main", "physics-main", True)]


def test_deploy_push_can_skip_tests_explicitly(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "tests_run", lambda c: events.append("tests"))
    monkeypatch.setattr(
        tasks,
        "_push_repositories",
        lambda c, main_branch, physics_branch, tags: events.append("push"),
    )

    tasks.deploy_push.body(DummyContext(), skip_tests=True)

    assert events == ["push"]


def test_deploy_push_does_not_push_when_tests_fail(monkeypatch):
    events = []
    _patch_branches(monkeypatch)

    def fail_tests(c):
        events.append("tests")
        raise RuntimeError("tests failed")

    monkeypatch.setattr(tasks, "tests_run", fail_tests)
    monkeypatch.setattr(
        tasks,
        "_push_repositories",
        lambda c, main_branch, physics_branch, tags: events.append("push"),
    )

    with pytest.raises(RuntimeError, match="tests failed"):
        tasks.deploy_push.body(DummyContext())

    assert events == ["tests"]


def test_deploy_push_dry_run_does_not_run_tests_or_push(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "tests_run", lambda c: events.append("tests"))
    monkeypatch.setattr(
        tasks,
        "_push_repositories",
        lambda c, main_branch, physics_branch, tags: events.append("push"),
    )

    tasks.deploy_push.body(DummyContext(), dry_run=True)

    assert events == []


def test_deploy_release_runs_tests_before_git_mutations(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "_read_version", lambda path: "1.2.3.4")
    monkeypatch.setattr(
        tasks,
        "_write_version",
        lambda path, version: events.append(("write", path, version)),
    )
    monkeypatch.setattr(tasks, "_repo_status", lambda c, repo_path: "")
    monkeypatch.setattr(tasks, "_git_stdout", lambda c, repo_path, command: "")
    monkeypatch.setattr(tasks, "tests_run", lambda c: events.append("tests"))
    monkeypatch.setattr(tasks, "_create_github_release", lambda c, tag_name: None)
    monkeypatch.setattr(
        tasks,
        "_git",
        lambda c, repo_path, command, hide=False: events.append(
            ("git", repo_path, command)
        )
        or SimpleNamespace(stdout=""),
    )

    tasks.deploy_release.body(DummyContext(), revision=True)

    git_index = next(index for index, event in enumerate(events) if event[0] == "git")
    assert events[:3] == [
        ("write", tasks.MAIN_SETUP_PATH, "1.2.3.5"),
        ("write", tasks.PHYSICS_SETUP_PATH, "1.2.3.5"),
        "tests",
    ]
    assert events.index("tests") < git_index


def test_deploy_release_creates_github_release_after_pushing_main_tag(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "_read_version", lambda path: "1.2.3.4")
    monkeypatch.setattr(tasks, "_write_version", lambda path, version: None)
    monkeypatch.setattr(tasks, "_repo_status", lambda c, repo_path: "")
    monkeypatch.setattr(tasks, "_git_stdout", lambda c, repo_path, command: "")
    monkeypatch.setattr(tasks, "tests_run", lambda c: None)
    monkeypatch.setattr(
        tasks,
        "_git",
        lambda c, repo_path, command, hide=False: events.append((repo_path, command))
        or SimpleNamespace(stdout=""),
    )
    monkeypatch.setattr(
        tasks, "_create_github_release", lambda c, tag_name: events.append(("release", tag_name))
    )
    monkeypatch.setattr(
        tasks, "_push_repositories", lambda *args, **kwargs: events.append(("branches",))
    )

    tasks.deploy_release.body(DummyContext(), revision=True)

    main_tag_push = (tasks.REPO_ROOT, "push origin v1.2.3.5")
    assert events.index(main_tag_push) < events.index(("release", "v1.2.3.5"))
    assert events.index(("release", "v1.2.3.5")) < events.index(("branches",))


def test_deploy_release_restores_versions_when_tests_fail(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    monkeypatch.setattr(tasks, "_read_version", lambda path: "1.2.3.4")
    monkeypatch.setattr(
        tasks,
        "_write_version",
        lambda path, version: events.append(("write", path, version)),
    )
    monkeypatch.setattr(tasks, "_repo_status", lambda c, repo_path: "")
    monkeypatch.setattr(tasks, "_git_stdout", lambda c, repo_path, command: "")

    def fail_tests(c):
        events.append("tests")
        raise RuntimeError("tests failed")

    monkeypatch.setattr(tasks, "tests_run", fail_tests)
    monkeypatch.setattr(
        tasks,
        "_git",
        lambda c, repo_path, command, hide=False: events.append(
            ("git", repo_path, command)
        ),
    )

    with pytest.raises(RuntimeError, match="tests failed"):
        tasks.deploy_release.body(DummyContext(), revision=True)

    assert events == [
        ("write", tasks.MAIN_SETUP_PATH, "1.2.3.5"),
        ("write", tasks.PHYSICS_SETUP_PATH, "1.2.3.5"),
        "tests",
        ("write", tasks.MAIN_SETUP_PATH, "1.2.3.4"),
        ("write", tasks.PHYSICS_SETUP_PATH, "1.2.3.4"),
    ]


def test_deploy_release_rejects_mismatched_versions_before_writing(monkeypatch):
    events = []
    _patch_branches(monkeypatch)
    versions = {
        tasks.MAIN_SETUP_PATH: "1.2.3.4",
        tasks.PHYSICS_SETUP_PATH: "1.2.3.3",
    }
    monkeypatch.setattr(tasks, "_read_version", lambda path: versions[path])
    monkeypatch.setattr(
        tasks,
        "_write_version",
        lambda path, version: events.append(("write", path, version)),
    )

    with pytest.raises(Exception, match="versions differ"):
        tasks.deploy_release.body(DummyContext(), revision=True)

    assert events == []
