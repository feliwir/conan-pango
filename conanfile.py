import os
import shutil
import glob

from conans import ConanFile, tools, Meson, VisualStudioBuildEnvironment


class PangoConan(ConanFile):
    name = "pango"
    version = "1.44.7"
    license = "MIT"
    url = "https://github.com/bincrafters/conan-pango"
    description = "Internationalized text layout and rendering library"
    homepage = "https://www.pango.org/"
    author = "Bincrafters"
    topics = ("conan", "fontconfig", "fonts", "freedesktop")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": True, "fPIC": True}
    generators = "pkg_config"
    exports = "LICENSE"
    exports_sources = ["patches/*.patch"]
    _source_subfolder = "source_subfolder"
    _autotools = None

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def config_option(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _meson_required(self):
        from six import StringIO 
        mybuf = StringIO()
        if self.run("meson -v", output=mybuf, ignore_errors=True) != 0:
            return True
        return tools.Version(mybuf.getvalue()) < tools.Version('0.53.0')

    def build_requirements(self):
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        if self._meson_required:
            self.build_requires("meson/0.53.2")

    def requirements(self):
        self.requires("freetype/2.10.1")
        if self.settings.os != "Windows":
            self.requires("fontconfig/2.13.91@conan/stable")
        self.requires("cairo/1.17.2@bincrafters/stable")
        self.requires("harfbuzz/2.6.4@bincrafters/stable")
        self.requires("glib/2.64.0@bincrafters/stable")
        self.requires("fribidi/1.0.5@bincrafters/stable")

    def source(self):
        source_url = "https://github.com/GNOME/pango/archive/{}.tar.gz"
        sha256 = "695bbf21fc3ac0f0ff12c9566eea6e4a169d98a3f0660b357ce208dbd21b0a4b"
        tools.get(source_url.format(self.version), sha256=sha256)
        extrated_dir = self.name + "-" + self.version
        os.rename(extrated_dir, self._source_subfolder)

    def _configure_meson(self):
        defs = dict()
        defs["introspection"] = "false"
        meson = Meson(self)
        meson.configure(build_folder="build", source_folder=self._source_subfolder, defs=defs, args=['--wrap-mode=nofallback'])
        return meson

    def build(self):
        for filename in sorted(glob.glob("patches/*.patch")):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)
        for package in self.deps_cpp_info.deps:
            lib_path = self.deps_cpp_info[package].rootpath
            for dirpath, _, filenames in os.walk(lib_path):
                for filename in filenames:
                    if filename.endswith('.pc'):
                        if filename in ["cairo.pc", "fontconfig.pc"]:
                            continue
                        shutil.copyfile(os.path.join(dirpath, filename), filename)
                        tools.replace_prefix_in_pc_file(filename, tools.unix_path(lib_path) if self.settings.os == 'Windows' else lib_path)
        meson_build = os.path.join(self._source_subfolder, "meson.build")
        tools.replace_in_file(meson_build, "subdir('tests')", "")
        tools.replace_in_file(meson_build, "subdir('tools')", "")
        tools.replace_in_file(meson_build, "subdir('utils')", "")
        tools.replace_in_file(meson_build, "subdir('examples')", "")
        tools.replace_in_file(meson_build, "add_project_arguments([ '-FImsvc_recommended_pragmas.h' ], language: 'c')", "")
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.build()

    def _fix_library_names(self):
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(os.path.join(self.package_folder, "lib")):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.install()
        self._fix_library_names()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join(self.package_folder, "include", "pango-1.0"))
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["m", "pthread"])
        self.env_info.PATH.append(os.path.join(self.package_folder, 'bin'))
