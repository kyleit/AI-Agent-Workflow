from devteam.domain.seats.write_set import WriteSet


def test_identical_dirs_overlap():
    assert WriteSet(("src",)).overlaps(WriteSet(("src",)))


def test_parent_child_overlap():
    assert WriteSet(("src",)).overlaps(WriteSet(("src/app",)))
    assert WriteSet(("src/app",)).overlaps(WriteSet(("src",)))


def test_root_overlaps_everything():
    assert WriteSet((".",)).overlaps(WriteSet(("anything",)))


def test_siblings_do_not_overlap():
    assert not WriteSet(("src",)).overlaps(WriteSet(("app",)))


def test_prefix_string_not_path_boundary():
    # "src" must not overlap "srclib" (not a path-segment boundary)
    assert not WriteSet(("src",)).overlaps(WriteSet(("srclib",)))
