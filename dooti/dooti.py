import os.path

import objc
from AppKit import NSWorkspace  # pylint: disable=no-name-in-module
from Foundation import NSURL, NSArray  # pylint: disable=no-name-in-module
from UniformTypeIdentifiers import (  # pylint: disable=no-name-in-module
    UTTagClassFilenameExtension,
    UTType,
)


class ExtHasNoRegisteredUTI(ValueError):
    """
    Raised when trying to set a handler for a file extension
    that does not have an associated registered UTI.
    """


class ApplicationNotFound(ValueError):
    """
    Raised when a handler reference cannot be resolved.
    """


class BundleURLNotFound(ApplicationNotFound):
    """
    Raised when a bundle ID is not registered on the system.
    """


class Dooti:
    """
    Wrapper for macOS system API to manage default handlers on macOS 12.0+.
    """

    def __init__(self, workspace=None):
        if workspace is None:
            workspace = NSWorkspace.sharedWorkspace()

        self.workspace = workspace

    @staticmethod
    def ext_to_utis(ext: str) -> NSArray:
        """
        Returns all UTI associated with specified file extension.
        If the extension is not registered with MacOS, will return
        a dynamic UTI as first and only element.

        :param str ext: file extension to look up associated UTI for
        """
        return UTType.typesWithTag_tagClass_conformingToType_(
            ext, UTTagClassFilenameExtension, objc.nil
        )

    def set_default_uti(self, uti: str | UTType, app: str) -> None:
        """
        Sets a default handler for a specific UTI.

        :param str | UTType uti: UTI to set the default handler for
        :param str app: absolute filesystem path, name or bundle ID of the handler
        """
        if not isinstance(uti, UTType):
            uti = UTType.importedTypeWithIdentifier_(uti)

        path = self.get_app_path(app)

        self.workspace.setDefaultApplicationAtURL_toOpenContentType_completionHandler_(
            path, uti, objc.nil
        )

    def set_default_scheme(self, scheme: str, app: str) -> None:
        """
        Sets a default handler for a specific URL scheme.

        :param str scheme: URL scheme to set the default handler for
        :param str app: absolute filesystem path, name or bundle ID of the handler
        """

        path = self.get_app_path(app)

        self.workspace.setDefaultApplicationAtURL_toOpenURLsWithScheme_completionHandler_(
            path, scheme, objc.nil
        )

    def set_default_ext(self, ext: str, app: str, allow_dynamic: bool = False) -> None:
        """
        Sets a default handler for all UTI registered to a file extension.

        :param str ext: file extension to set the default handler for
        :param str app: absolute filesystem path, name or bundle ID of the handler
        :param bool allow_dynamic: whether to allow dynamic UTIs (default False)

        :raises:
            ExtHasNoRegisteredUTI if the file extension is unknown to MacOS and not allowing dynamic UTI
        """
        utis = Dooti.ext_to_utis(ext)

        if self.is_dynamic_uti(utis[0]) and not allow_dynamic:
            raise ExtHasNoRegisteredUTI(
                f"No UTI are registered for file extension '{ext}'. "
                "To force using a dynamic UTI, pass allow_dynamic=True."
            )

        for uti in utis:
            self.set_default_uti(uti, app)

    def is_dynamic_uti(self, ext_or_uti: str | UTType) -> bool:
        """
        Checks whether a UTI is dynamic/whether a file extension is not
        associated with at least one registered UTI.

        :param str | UTType ext_or_uti: UTI or file extension to check
        """
        if isinstance(ext_or_uti, str):
            ext_or_uti = Dooti.ext_to_utis(ext_or_uti)[0]
        return str(ext_or_uti).startswith("dyn.")

    def get_default_uti(self, uti: str | UTType) -> str | None:
        """
        Returns the filesystem path to the default handler for the
        specified UTI.

        :param str | UTType uti: UTI to look up the default handler path for
        """

        if not isinstance(uti, UTType):
            uti = UTType.importedTypeWithIdentifier_(uti)

        handler = self.workspace.URLForApplicationToOpenContentType_(uti)

        if not handler:
            return None

        # name = handler.lastPathComponent()[:-4]

        return handler.fileSystemRepresentation().decode()

    def get_default_ext(self, ext: str) -> str | None:
        """
        Returns the filesystem path to the default handler for the
        specified file extension.

        :param str ext: filename extension to look up the default handler path for
        """
        utis = Dooti.ext_to_utis(ext)

        # assume the handler is the same for all types (sensible?)
        # even if the extension was not registered, utis will still contain
        # a dynamic UTI, so we do not need to check for an empty iterator
        handler = self.workspace.URLForApplicationToOpenContentType_(utis[0])

        if not handler:
            return None

        # name = handler.lastPathComponent()[:-4]

        return handler.fileSystemRepresentation().decode()

    def get_default_scheme(self, scheme: str) -> str | None:
        """
        Returns the filesystem path to the default handler for the
        specified URL scheme.

        :param str ext: filename extension to look up the default handler path for
        """
        if "file" == scheme:
            raise ValueError("The file:// scheme cannot be looked up.")

        url = NSURL.URLWithString_(scheme + "://nonexistant")

        handler = self.workspace.URLForApplicationToOpenURL_(url)

        if not handler:
            return None

        # name = handler.lastPathComponent()[:-4]

        return handler.fileSystemRepresentation().decode()

    def get_app_path(self, app: str) -> NSURL:
        """
        Returns a URL (filesystem path prefixed with 'file://' scheme) to an
        application specified by name, absolute path or bundle ID.

        :param str app: name, absolute filesystem path or bundle ID to look up the URL for

        :raises:
            ApplicationNotFound: when no matching application was found
        """
        if "/" == app[0]:
            return NSURL.fileURLWithPath_(app)

        try:
            return self.bundle_to_url(app)
        except BundleURLNotFound:
            pass

        try:
            return self.name_to_url(app)
        except ApplicationNotFound as exc:
            raise ApplicationNotFound(
                f"Could not find an application matching the description '{app}'."
            ) from exc

    def bundle_to_url(self, bundle_id: str) -> NSURL:
        """
        Returns a URL (filesystem path prefixed with 'file://' scheme) to an
        application with the specified bundle ID.

        :param str bundle_id: bundle ID to look up the URL for

        :raises:
            BundleURLNotFound: when no application with specified bundle ID was found
        """
        path = self.workspace.URLForApplicationWithBundleIdentifier_(bundle_id)

        if path is None:
            raise BundleURLNotFound(
                f"There is no bundle with the identifier '{bundle_id}'."
            )

        return path

    def name_to_url(self, app_name: str) -> NSURL:
        """
        Returns a URL (filesystem path prefixed with 'file://' scheme) to an
        application with the specified name.

        :param str app_name: application name to look up the URL for

        :raises:
            ApplicationNotFound: when no application with specified bundle ID was found
        """
        path = self.workspace.fullPathForApplication_(app_name)

        if path is None:
            raise ApplicationNotFound(
                f"Could not find an application named '{app_name}'."
            )

        return NSURL.fileURLWithPath_(path)

    def path_to_url(self, path: str, skip_check: bool = False) -> NSURL:
        """
        Translates an absolute filesystem path to a URL.

        :param str path: absolute filesystem path to translate
        :param bool skip_check: override check if the target exists and is a directory

        :raises:
            ApplicationNotFound: when no application with specified bundle ID was found
        """

        if not skip_check and not os.path.isdir(path):
            raise ApplicationNotFound(f"Could not find an application in '{path}'.")

        return NSURL.fileURLWithPath_(path)
