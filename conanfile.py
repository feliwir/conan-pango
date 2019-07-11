#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import glob

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

    def build_requirements(self):
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        if not tools.which("meson"):
            self.build_requires("meson_installer/0.50.0@bincrafters/stable")

    def requirements(self):
        # FIXME : package fribidi
        self.requires("freetype/2.10.0@bincrafters/stable")
        if self.settings.os != "Windows":
            self.requires("fontconfig/2.13.91@conan/stable")
        self.requires("cairo/1.17.2@bincrafters/stable")
        self.requires("harfbuzz/2.4.0@bincrafters/stable")
        self.requires("glib/2.58.3@bincrafters/stable")

    def source(self):
        source_url = "https://github.com/GNOME/pango/archive/{}.tar.gz"
        sha256 = "8d07021cc1eb622fc8b5ef5b96602a880964cd0b57d9996119815c032830af5d"
        tools.get(source_url.format(self.version), sha256=sha256)
        extrated_dir = self.name + "-" + self.version
        os.rename(extrated_dir, self._source_subfolder)

    def _configure_meson(self):
        defs = dict()
        defs["gir"] = "false"
        meson = Meson(self)
        meson.configure(build_folder="build", source_folder=self._source_subfolder, defs=defs)
        return meson

    def _copy_pkg_config(self, name):
        root = self.deps_cpp_info[name].rootpath
        pc_dir = os.path.join(root, 'lib', 'pkgconfig')
        pc_files = glob.glob('%s/*.pc' % pc_dir)
        if not pc_files:  # zlib store .pc in root
            pc_files = glob.glob('%s/*.pc' % root)
        for pc_name in pc_files:
            new_pc = os.path.basename(pc_name)
            self.output.warn('copy .pc file %s' % os.path.basename(pc_name))
            shutil.copy(pc_name, new_pc)
            prefix = tools.unix_path(root) if self.settings.os == 'Windows' else root
            tools.replace_prefix_in_pc_file(new_pc, prefix)

    def build(self):
        self._copy_pkg_config("glib")
        self._copy_pkg_config("cairo")
        meson_build = os.path.join(self._source_subfolder, "meson.build")
        tools.replace_in_file(meson_build, "subdir('tests')", "")
        tools.replace_in_file(meson_build, "subdir('tools')", "")
        tools.replace_in_file(meson_build, "subdir('utils')", "")
        tools.replace_in_file(meson_build, "subdir('examples')", "")
        tools.replace_in_file(meson_build, "add_project_arguments([ '-FImsvc_recommended_pragmas.h' ], language: 'c')", "")
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

