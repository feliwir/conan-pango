#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil

from conans import ConanFile, tools, Meson

class PangoConan(ConanFile):
    name = "pango"
    version = "1.43.0"
    license = "MIT"
    url = "https://github.com/bincrafters/conan-pango"
    description = "Internationalized text layout and rendering library"
    homepage = "https://www.pango.org/"
    author = "Bincrafters"
    topics = ("conan", "fontconfig", "fonts", "freedesktop")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    generators = "pkg_config"
    exports = "LICENSE"
    _source_subfolder = "source_subfolder"
    _autotools = None

    def config_option(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("meson_installer/0.50.0@bincrafters/stable")
        self.requires("freetype/2.10.0@bincrafters/stable")
        self.requires("fontconfig/2.13.91@conan/stable")
        self.requires("cairo/1.17.2@bincrafters/stable")
        self.requires("harfbuzz/2.4.0@bincrafters/stable")

    def source(self):
        source_url = "https://github.com/GNOME/pango/archive/{}.tar.gz"
        sha256 = "8d07021cc1eb622fc8b5ef5b96602a880964cd0b57d9996119815c032830af5d"
        tools.get(source_url.format(self.version), sha256=sha256)
        extrated_dir = self.name + "-" + self.version
        os.rename(extrated_dir, self._source_subfolder)

    def _configure_meson(self):
        # FIXME : need components feature
        glib_pc = os.path.join(self.deps_cpp_info["glib"].rootpath, "lib", "pkgconfig")
        cairo_pc = os.path.join(self.deps_cpp_info["cairo"].rootpath, "lib", "pkgconfig")
        pkg_config_paths = [glib_pc, cairo_pc, self.source_folder]
        defs = dict()
        defs["gir"] = "false"
        meson = Meson(self)
        meson.configure(build_folder="build", source_folder=self._source_subfolder,
                        pkg_config_paths=pkg_config_paths, defs=defs)
        return meson

    def build(self):
        shutil.move("freetype.pc", "freetype2.pc")
        meson = self._configure_meson()
        meson.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join(self.package_folder, "include", "pango-1.0"))
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["m", "pthread"])
        self.env_info.PATH.append(os.path.join(self.package_folder, 'bin'))

