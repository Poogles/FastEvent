{ pkgs ? import <nixpkgs> {}, system ? builtins.currentSystem, }:

# Setup pinned items like dependencies and static env vars.
let
  pinned = import (fetchTarball {
      name = "nixos-25.0";
      url = https://github.com/NixOS/nixpkgs/archive/refs/tags/25.05.tar.gz;
  }) {};

  systemBuildExports = (
    with pinned;
    {
      x86_64-linux = ''
        export LD_LIBRARY_PATH="${pinned.stdenv.cc.cc.lib}/lib/"
      '';
      aarch64-darwin = ''
        export DYLD_LIBRARY_PATH="${pinned.stdenv.cc.cc.lib}/lib/"
      '';
    }
  );

# Install our dependencies defined above.
in
  pkgs.mkShell {
    name = "projects.fastevent";

    buildInputs = [
      pinned.autoPatchelfHook
      pinned.direnv
      pinned.git
      pinned.pre-commit
      pinned.protobuf
      pinned.python312
      pinned.stdenv.cc.cc.lib   # required for numpy and libstdc++.so.6
      pinned.poetry
    ];

    nativeBuildInputs = [ pinned.autoPatchelfHook ];

    # Set the required env vars to run the app. 
    NIX_LDFLAGS = if system ? "x86_64-linux" then [ "-lstdc++"] else [];
    LANG="en_UK.UTF-8";

    shellHook = ''
      PATH="${pinned.poetry}:${pinned.python312}/bin:$PATH";
    '' + systemBuildExports.${system};
}
