# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class KhronosOpenCLICDLoaderConan(ConanFile):
    name = "khronos-opencl-icd-loader"
    version = "20190827"
    description = "The OpenCL ICD Loader"
    topics = ("conan", "opencl", "opencl-icd-loader", "build-system",
              "icd-loader")
    url = "https://github.com/bincrafters/conan-khronos-opencl-icd-loader"
    homepage = "https://github.com/KhronosGroup/OpenCL-ICD-Loader"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "Apache-2.0"
    exports = ["LICENSE.md"]
    exports_sources = [
        "CMakeLists.txt",
        "0001-OpenCL-Headers-Remove-ABI-hackery.patch",
        "0002-Work-around-missing-declarations-in-MinGW-headers.patch",
    ]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"fPIC": [True, False], "shared": [True, False]}
    default_options = {"fPIC": True, "shared": False}
    requires = "khronos-opencl-headers/20190806@bincrafters/stable"
    short_paths = True
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        commit = "6c03f8b58fafd9dd693eaac826749a5cfad515f8"
        sha256 = "c94d5bb6dc980c4d41d73e2b81663a19aabe494e923e2d0eec72a4c95b318438"
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, commit),
                  sha256=sha256)
        extracted_dir = "OpenCL-ICD-Loader-" + commit
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        if self._is_mingw():
            cmake.definitions.update({
                "CMAKE_C_STANDARD": "99",
                "CMAKE_C_STANDARD_REQUIRED": True,
                "OPENCL_ICD_LOADER_REQUIRE_WDK": False,
            })
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def _is_mingw(self):
        subsystem_matches = self.settings.get_safe("os.subsystem") in [
            "msys", "msys2"
        ]
        compiler_matches = self.settings.os == "Windows" and self.settings.compiler == "gcc"
        return subsystem_matches or compiler_matches

    def build(self):
        tools.patch(base_path=self._source_subfolder,
                    patch_file="0001-OpenCL-Headers-Remove-ABI-hackery.patch")
        if self._is_mingw():
            tools.patch(
                base_path=self._source_subfolder,
                patch_file=
                "0002-Work-around-missing-declarations-in-MinGW-headers.patch")
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE",
                  dst="licenses",
                  src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "dl"])
        elif self.settings.os == "Windows" and \
             self.settings.get_safe("os.subsystem") != "wsl":
            self.cpp_info.libs.append("cfgmgr32")
