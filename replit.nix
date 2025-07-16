{ pkgs }: {
  deps = [
    pkgs.glibcLocales
    pkgs.python310Full
    pkgs.python310Packages.pip
    pkgs.python310Packages.setuptools
    pkgs.python310Packages.wheel
  ];
}