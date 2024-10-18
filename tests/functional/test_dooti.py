import contextlib

import pytest
from UniformTypeIdentifiers import UTType

from dooti.dooti import (
    ApplicationNotFound,
    BundleURLNotFound,
    Dooti,
    ExtHasNoRegisteredUTI,
)
from tests.helpers import get_ext_handler, get_scheme_handler


@pytest.fixture(scope="module")
def dooti():
    return Dooti()


@pytest.mark.parametrize(
    "ext,expected",
    (
        ("pdf", {"com.adobe.pdf"}),
        ("fooobaar", {"dyn.age80q55tr7vgc2pw"}),
        ("fooo.baar", False),
    ),
)
def test_ext_to_utis(ext, expected):
    utis = {str(uti) for uti in Dooti.ext_to_utis(ext)}
    if expected:
        assert expected <= utis
    else:
        assert not utis


@pytest.mark.destructive_test
@pytest.mark.parametrize(
    "ext,uti,new",
    (
        ("txt", "public.plain-text", "Script Editor"),
        (
            "txt",
            UTType.importedTypeWithIdentifier_("public.plain-text"),
            "Script Editor",
        ),
    ),
)
def test_set_default_uti(dooti, ext, uti, new):
    curr = get_ext_handler(ext)
    new = dooti.get_app_path(new).path()
    assert curr != new
    try:
        res = dooti.set_default_uti(uti, new)
        assert res is None
        assert get_ext_handler(ext) == new
    finally:
        dooti.set_default_uti(uti, curr)
        assert get_ext_handler(ext) == curr


@pytest.mark.destructive_test
@pytest.mark.parametrize(
    "scheme,new",
    (("ftp", "Safari"),),
)
def test_set_default_scheme(dooti, scheme, new):
    curr = get_scheme_handler(scheme)
    new = dooti.get_app_path(new).path()
    assert curr != new
    try:
        res = dooti.set_default_scheme(scheme, new)
        assert res is None
        assert get_scheme_handler(scheme) == new
    finally:
        dooti.set_default_scheme(scheme, curr)
        assert get_scheme_handler(scheme) == curr


@pytest.mark.destructive_test
@pytest.mark.parametrize(
    "ext,new",
    (("txt", "Script Editor"),),
)
def test_set_default_ext(dooti, ext, new):
    curr = get_ext_handler(ext)
    new = dooti.get_app_path(new).path()
    assert curr != new
    try:
        res = dooti.set_default_ext(ext, new)
        assert res is None
        assert get_ext_handler(ext) == new
    finally:
        dooti.set_default_ext(ext, curr)
        assert get_ext_handler(ext) == curr


@pytest.mark.destructive_test
def test_set_default_scheme_dynamic(dooti):
    with pytest.raises(ExtHasNoRegisteredUTI):
        dooti.set_default_ext("fooobaaarr", "Preview")


@pytest.mark.parametrize(
    "ext_or_uti,expected",
    (
        ("pdf", False),
        ("baaaaaz", True),
        (UTType.importedTypeWithIdentifier_("com.adobe.pdf"), False),
        (UTType.importedTypeWithIdentifier_("dyn.age80q55tr7vgc2pw"), True),
    ),
)
def test_is_dynamic_uti(dooti, ext_or_uti, expected):
    assert dooti.is_dynamic_uti(ext_or_uti) is expected


@pytest.mark.parametrize(
    "uti,ext",
    (
        (UTType.importedTypeWithIdentifier_("com.adobe.pdf"), "pdf"),
        ("com.adobe.pdf", "pdf"),
        ("org.fooo.baar", None),
    ),
)
def test_get_default_uti(dooti, uti, ext):
    res = dooti.get_default_uti(uti)
    if ext:
        assert res == get_ext_handler(ext)
    else:
        assert res is None


@pytest.mark.parametrize("ext,expected", (("pdf", True), ("fooobaaar", False)))
def test_get_default_ext(dooti, ext, expected):
    res = dooti.get_default_ext(ext)
    if expected:
        assert res == get_ext_handler(ext)
    else:
        assert res is None


@pytest.mark.parametrize(
    "scheme,expected",
    (
        ("https", True),
        ("fooobaaar", False),
        ("file", pytest.raises(ValueError, match=".*cannot be looked up")),
    ),
)
def test_get_default_scheme(dooti, scheme, expected):
    if isinstance(expected, bool):
        ctx = contextlib.nullcontext()
    else:
        ctx = expected
    with ctx:
        res = dooti.get_default_scheme(scheme)
        if expected:
            assert res == get_scheme_handler(scheme)
        else:
            assert res is None


@pytest.mark.parametrize(
    "app,expected",
    (
        ("Preview", "/System/Applications/Preview.app"),
        ("com.apple.preview", "/System/Applications/Preview.app"),
        ("/System/Applications/Preview.app", "/System/Applications/Preview.app"),
        (
            "org.foo.baaar",
            pytest.raises(
                ApplicationNotFound,
                match="Could not find an application matching.*org\\.foo\\.baaar.*",
            ),
        ),
    ),
)
def test_get_app_path(dooti, app, expected):
    if isinstance(expected, str):
        ctx = contextlib.nullcontext()
    else:
        ctx = expected
    with ctx:
        assert dooti.get_app_path(app).path() == expected


@pytest.mark.parametrize(
    "bundle,expected",
    (
        ("com.apple.preview", "/System/Applications/Preview.app"),
        (
            "org.foo.baaar",
            pytest.raises(
                BundleURLNotFound, match="There is no bundle.*org\\.foo\\.baaar.*"
            ),
        ),
    ),
)
def test_bundle_to_url(dooti, bundle, expected):
    if isinstance(expected, str):
        ctx = contextlib.nullcontext()
    else:
        ctx = expected
    with ctx:
        assert dooti.bundle_to_url(bundle).path() == expected


@pytest.mark.parametrize(
    "name,expected",
    (
        ("Preview", "/System/Applications/Preview.app"),
        (
            "this should not exist",
            pytest.raises(
                ApplicationNotFound,
                match="Could not find an application named 'this should not exist'.*",
            ),
        ),
    ),
)
def test_name_to_url(dooti, name, expected):
    if isinstance(expected, str):
        ctx = contextlib.nullcontext()
    else:
        ctx = expected
    with ctx:
        assert dooti.name_to_url(name).path() == expected


@pytest.mark.parametrize(
    "path,skip_check,expected",
    (
        (
            "/System/Applications/Preview.app",
            False,
            "/System/Applications/Preview.app",
        ),
        (
            "/System/Applications/foo bar.app",
            False,
            pytest.raises(
                ApplicationNotFound, match="Could not find an application in '/System.*"
            ),
        ),
        (
            "/System/Applications/foo bar.app",
            True,
            "/System/Applications/foo bar.app",
        ),
    ),
)
def test_path_to_url(dooti, path, skip_check, expected):
    if isinstance(expected, str):
        ctx = contextlib.nullcontext()
    else:
        ctx = expected
    with ctx:
        assert dooti.path_to_url(path, skip_check=skip_check).path() == expected
