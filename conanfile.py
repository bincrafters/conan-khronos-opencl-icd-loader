from conans import ConanFile, CMake, tools
import os


class KhronosOpenCLICDLoaderConan(ConanFile):
    name = "khronos-opencl-icd-loader"
    version = "20191007"
    description = "The OpenCL ICD Loader"
    topics = ("conan", "opencl", "opencl-icd-loader", "build-system",
              "icd-loader")
    url = "https://github.com/bincrafters/conan-khronos-opencl-icd-loader"
    homepage = "https://github.com/KhronosGroup/OpenCL-ICD-Loader"
    license = "Apache-2.0"
    exports_sources = [
        "CMakeLists.txt",
        "0001-Work-around-missing-declarations-in-MinGW-headers.patch",
        "0002-link-windows-libs.patch"
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
        del self.settings.compiler.cppstd

    def source(self):
        commit = "978b4b3a29a3aebc86ce9315d5c5963e88722d03"
        sha256 = "0c14bf890bd198ef5a814b5b7ed57b69e890b0c0a1bcfba8fdad996fa1a97fc7"
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, commit),
                  sha256=sha256)
        extracted_dir = "OpenCL-ICD-Loader-" + commit
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["USE_DYNAMIC_VCXX_RUNTIME"] = True
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
        if self._is_mingw():
            tools.patch(
                base_path=self._source_subfolder,
                patch_file=
                "0001-Work-around-missing-declarations-in-MinGW-headers.patch")
            tools.patch(
                base_path=self._source_subfolder,
                patch_file="0002-link-windows-libs.patch"
            )
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
            self.cpp_info.libs += "cfgmgr32", "ole32"
